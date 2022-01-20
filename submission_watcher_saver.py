import os
import django

from time import sleep
from subprocess import call
from typing import List
from datetime import timedelta
from pycodestyle import Checker


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "autojudge.settings")
django.setup()

from judge import models, handler  # noqa: E402

CONTENT_DIRECTORY = 'content'
TMP_DIRECTORY = 'tmp'
TESTCASE_DIRECTORY = 'testcase'
CLANG_JUDGE_DIRECTORY = 'judgeClangTool'
MONITOR_DIRECTORY = os.path.join(CONTENT_DIRECTORY, TMP_DIRECTORY)
OUTPUT_DIRECTORY = os.path.join(CONTENT_DIRECTORY, TESTCASE_DIRECTORY)
CLANG_TOOL_DIRECTORY = os.path.join(CONTENT_DIRECTORY, CLANG_JUDGE_DIRECTORY)
DOCKER_IMAGE_NAME = 'autojudge_docker'

LS: List[str] = []
# Re-check the status of the submission folder if the number of unscored submissions
# is less than REFRESH_LS_TRIGGER
REFRESH_LS_TRIGGER = 5
# Sleep duration if number of unscored submissions is less than REFRESH_LS_TRIGGER
SLEEP_DUR_BEFORE_REFRESH = 10


def _compute_lint_score(report):
    if len(report.lines) > 0:
        score = 10.0 * (1 - report.total_errors / len(report.lines))
        return max(0.0, score)


def saver(sub_id):
    update_lb = False
    if not os.path.exists(os.path.join(MONITOR_DIRECTORY, 'sub_run_' + sub_id + '.txt')):
        print("Internal Error: Can't find sub run txt file")
        return True

    clang_tool_msg=""
    try:
        #Checking if any tool output exists or not
        if os.path.isfile(os.path.join(MONITOR_DIRECTORY,  'sub_clangjudge_'+sub_id+'.log')):
            #If so copy output to variable
            with open(os.path.join(MONITOR_DIRECTORY, 'sub_clangjudge_'+sub_id+'.log'),'r',encoding='utf-8') as f:
                clang_tool_msg=str(f.read())

            #Remove file after copying output
            os.remove(os.path.join(MONITOR_DIRECTORY,'sub_clangjudge_'+sub_id+'.log'))

        #TODO:Handle displaying of errors when clang tool runs into a general compilation error [ should be displayed normally as error for submission ]
    except:
        print("Internal error: Clang tool log error")

    # Based on the result populate SubmsissionTestCase table and return the result
    with open(os.path.join(MONITOR_DIRECTORY, 'sub_run_' + sub_id + '.txt'), 'r') as f:
        # Assumed format to sub_run_ID.txt file
        # PROBLEM_CODE
        # SUBMISSION_ID
        # TESTCASEID VERDICT TIME MEMORY MESSAGE
        # TESTCASEID (If first VERDICT = CE)
        # Read the output into verdict, memory and time.
        try:
            lines = [line[:-1] for line in f.readlines()]
            problem = lines[0]
            submission = lines[1]
            skip_ce = 0
            testcase_id, verdict, time, memory, msg = [], [], [], [], []
        except Exception as err:
            print("Internal Error: Can't read sub txt file")
        for line in lines[2:]:
            try:
                sep = line.split(' ', maxsplit=4)
                testcase_id.append(sep[0])
                if not skip_ce:
                    verdict.append(sep[1])
                    time.append(sep[2])
                    memory.append(sep[3])
            except Exception as err:
                print("Internal Error: Can't split sub txt string")
            if not skip_ce:
                try:
                    with open(os.path.join(MONITOR_DIRECTORY, sep[4])) as log_file:
                        msg.append(str(log_file.read()))
                except Exception as err:
                    msg.append("Output has invalid text")
                    verdict.pop()
                    verdict.append('RE')
                    print("Error: can't read log file")
                    print(sub_id)
                try:
                    os.remove(os.path.join(MONITOR_DIRECTORY, sep[4]))  # Remove after reading
                except Exception as err:
                    print("Internal Error: can't remove sub log file")
                # If compilation error or clang checks failed
                if len(sep[1]) > 2 or clang_tool_msg:
                    skip_ce = 1

    try:
        # Delete the file after reading
        os.remove(os.path.join(MONITOR_DIRECTORY, 'sub_run_' + sub_id + '.txt'))
    except Exception as err:
        print("Internal error: can't remove sub txt file")

    try:
        problem = models.Problem.objects.get(pk=problem)
        s = models.Submission.objects.get(pk=submission)
        if clang_tool_msg:
            s.clang_tool_msg = clang_tool_msg

        score_received = 0
        max_score = problem.max_score 
        correct_count = 0

        #If compilation fails then output error as normal error for test case
        if verdict[0] == 'CE0' or verdict[0] == 'CE1':
            clang_tool_msg="Tool Error:Compilation Failed.\nSee below for details why compilation failed"
            s.clang_tool_msg=clang_tool_msg
            s.verdict_type = verdict[0]
            verdict[0] = 'CE'
        elif verdict[0] == 'CE2':
            s.verdict_type = verdict[0]
            verdict[0] = 'F'

        for i in range(len(testcase_id)):
            st = models.SubmissionTestCase.objects.get(submission=submission,
                                                       testcase=testcase_id[i])
            if clang_tool_msg:
                st.verdict = verdict[0]
                st.memory_taken = int(memory[0])
                st.time_taken = timedelta(seconds=float(time[0]))
                st.message = msg[0]
            else:
                st.verdict = verdict[i]
                st.memory_taken = int(memory[i])
                st.time_taken = timedelta(seconds=float(time[i]))
                if verdict[i] == 'F' or verdict[i] == 'P':
                    if verdict[i] == 'P':
                        score_received += max_score
                        correct_count += 1
                    with open(os.path.join(OUTPUT_DIRECTORY, 'outputfile_' + testcase_id[i] + '.txt'),'r') as f:
                        st.msgfull = "Expected output:\n"+str(f.read())+"\nOutput:\n"+msg[i]
                        if models.TestCase.objects.get(pk=testcase_id[i]).public:
                            st.message = st.msgfull
                else:
                    st.msgfull = msg[i] if len(msg[i]) < 1000 else msg[i][:1000] + '\\nMessage Truncated'
                    if not models.TestCase.objects.get(pk=testcase_id[i]).public and verdict[i] == 'RE':
                        st.message = msg[i].splitlines()[-1]
                    else:
                        st.message = st.msgfull

            st.save()

        if not s.verdict_type:
            if correct_count == len(testcase_id):
                s.verdict_type = '0'
            else:
                s.verdict_type = 'RE0'

        s.judge_score = score_received

        if s.problem.contest.enable_linter_score:
            if s.file_type == '.py':
                checker = Checker(
                            os.path.join(CONTENT_DIRECTORY,
                                        'submissions', 'submission_{}.py'.format(submission)),
                            quiet=True)
                checker.check_all()
                s.linter_score = _compute_lint_score(checker.report)
        current_final_score = s.judge_score + s.poster_score + s.linter_score

        penalty_multiplier = 1.0
        # If the submission crosses soft deadline
        # Check if the submission has crossed the hard deadline
        # If yes, penalty_multiplier = 0
        # Else, penality_multiplier = 1 - num_of_days * penalty
        remaining_time = problem.contest.soft_end_datetime - s.timestamp
        if s.timestamp > problem.contest.soft_end_datetime:
            if s.timestamp > problem.contest.hard_end_datetime:
                penalty_multiplier = 0.0
            else:
                penalty_multiplier += remaining_time.days * problem.contest.penalty

        # If num_of_days * penalty > 1.0, then the score is clamped to zero
        s.final_score = max(0.0, current_final_score * penalty_multiplier)
        s.save()

        ppf, _ = models.PersonProblemFinalScore.objects.get_or_create(person=s.participant,
                                                                    problem=problem)
        if ppf.score <= s.final_score:
            # <= because otherwise when someone submits for the first time and scores 0
            # (s)he will not show up in leaderboard
            ppf.score = s.final_score
            update_lb = True
        ppf.save()

        if update_lb:
            # Update the leaderboard only if the submission improved the final score
            handler.update_leaderboard(problem.contest.pk, s.participant.email)
    except Exception as err:
        print("Internal Error: Database object create/update failed")

    return True


# Move to ./content
cur_path = os.getcwd()
os.chdir(os.path.join(cur_path, CONTENT_DIRECTORY))

out = 1
while out != 0:
    print("Building Docker image: {}....".format(DOCKER_IMAGE_NAME))
    # Build docker image using docker run
    out = call(['docker', 'build', '-t', DOCKER_IMAGE_NAME, './'])
    if out != 0:
        print("Build failed, retrying...")

# Move back to old directory
os.chdir(cur_path)

print("Docker image: {} built successfully!".format(DOCKER_IMAGE_NAME))

# Move to ./contest/judgeClangtool
os.chdir(os.path.join(cur_path, CLANG_TOOL_DIRECTORY))
call(['./build.sh'])

if os.path.isfile('clangjudge'):
    print("Clang Judge tool built successfully!")
else:
    print("Clang Judge tool build failed!")

# Move back to old directory
os.chdir(cur_path)

if not os.path.exists(MONITOR_DIRECTORY):
    os.makedirs(MONITOR_DIRECTORY)


while True:
    try:
        if len(LS) < REFRESH_LS_TRIGGER:
            # Neglect .log files in tmp/; these are for error
            # messages arising at any stage of the evaluation
            sleep(SLEEP_DUR_BEFORE_REFRESH)
            LS = [os.path.join(MONITOR_DIRECTORY, sub_file)
                for sub_file in os.listdir(MONITOR_DIRECTORY) if sub_file[:-4] != '.log']
            LS.sort(key=os.path.getctime)
    except Exception as err:
        print("Internal Error: Refresh trigger failed")

    if len(LS) > 0:
        try:
            sub_file = LS[0]  # The first file submission-wise
            sub_id = os.path.basename(sub_file)[8:-4]  # This is the submission ID
        except Exception as err:
            print("Internal Error: Couldn't get sub file name")

        # Move to content
        cur_dir = os.getcwd()
        os.chdir(os.path.join(cur_dir, CONTENT_DIRECTORY))

        # Run docker image
        print("INFO: evaluating submission: {}".format(sub_id))
        try:
            call(['docker', 'run', '--rm', '-v', '{}:/app'.format(os.getcwd()),
                '-e', 'SUB_ID={}'.format(sub_id), DOCKER_IMAGE_NAME])
        except Exception as err:
            print("Internal Error: Docker evaluation failed")

        # Come back to parent directory
        os.chdir(cur_dir)

        saver(sub_id)
        try:
            LS.remove(sub_file)
        except Exception as err:
            print("Internal Error: Remove sub file from list failed")
