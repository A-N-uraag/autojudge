import argparse
import subprocess

parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('--submission_config', type=str,
                    help="""Submission configuration file. Format of this file is:
                            PROBLEM_CODE
                            SUBMISSION_ID
                            SUBMISSION_FORMAT
                            CLANG_TOOL_FLAGS
                            TIME_LIMIT
                            MEMORY_LIMIT
                            TESTCASE_1_ID
                            TESTCASE_2_ID
                            TESTCASE_3_ID
                            ...""")
args = parser.parse_args()

def is_binary(fileName):
    try:
        with open(fileName) as check_file:  # try open file in text mode
            check_file.read()
            return False
    except:  # if fail then file is non-text (binary)
        return True

with open(args.submission_config) as f:
    sub_info = [x[:-1] for x in f.readlines()]

print(sub_info)

# Retain the first 2 lines alone
subprocess.call(['rm', args.submission_config])
with open(args.submission_config, "w") as stat_file:
    stat_file.write("{}\n{}\n".format(sub_info[0], sub_info[1]))


# Run clangjudge only for c/c++ submissions
clangjudge_flag = 0
if (sub_info[2]==".c" or sub_info[2]==".cpp") and sub_info[3]:
   
    isFileBinary=is_binary('submissions/submission_{}{}'.format(sub_info[1], sub_info[2]))
    #print(isFileBinary)

    if(isFileBinary):
        #print("binary found!")
        pass
    
    else:
        try:
            subprocess.check_output(['./judgeClangTool/clangjudge', sub_info[3],
                                'submissions/submission_{}{}'.format(sub_info[1], sub_info[2])])
        except subprocess.CalledProcessError as e:
            error_msg = str(e.output.decode('utf-8'))
            clangtool_log_file = 'sub_clangjudge_{}.log'.format(sub_info[1])
            with open('tmp/' + clangtool_log_file, "w") as log_file:
                log_file.write(error_msg)
            clangjudge_flag = 1

# First compile
try:
    subprocess.check_output(['./main_compiler.sh', sub_info[0],
                             'submission_{}{}'.format(sub_info[1], sub_info[2])],
                            stderr=subprocess.STDOUT)
except subprocess.CalledProcessError as e:  # If compilation fails, end this script here
    error_msg = str(e.output.decode('utf-8'))
    with open(args.submission_config, "a") as stat_file:
        for testcase_id in sub_info[6:]:
            log_file_name = 'sub_run_{}_{}.log'.format(sub_info[1], testcase_id)

            with open('tmp/' + log_file_name, "w") as log_file:
                log_file.write(error_msg)

            stat_file.write("{} {} 0 0 {}\n"
                            .format(testcase_id,
                                    'CE' if e.returncode == 1 else 'NA', log_file_name))
else:
    if clangjudge_flag == 0:
        subprocess.call(['./main_tester.sh'] + sub_info[0:2] + sub_info[4:])  # run tests
    else:
        with open(args.submission_config, "a") as stat_file:
            for testcase_id in sub_info[6:]:
                log_file_name = 'sub_run_{}_{}.log'.format(sub_info[1], testcase_id)

                with open('tmp/' + log_file_name, "w") as log_file:
                    log_file.write("Clang Checks failed. Program uses function that is not allowed.")

                stat_file.write("{} {} 0 0 {}\n".format(testcase_id, 'F', log_file_name))
    subprocess.call(['rm', 'submissions/submission_{}'.format(sub_info[1])])  # remove executable
