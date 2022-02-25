import argparse
import subprocess

parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('--submission_config', type=str,
                    help="""Submission configuration file. Format of this file is:
                            PROBLEM_CODE
                            IS_CMDLINE
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
    stat_file.write("{}\n{}\n".format(sub_info[0], sub_info[2]))


# Run clangjudge only for c/c++ submissions
clangjudge_flag = 0
if (sub_info[3]==".c" or sub_info[3]==".cpp") and sub_info[4]:
   
    isFileBinary=is_binary('submissions/submission_{}{}'.format(sub_info[2], sub_info[3]))
    #print(isFileBinary)

    if(isFileBinary):
        #print("binary found!")
        pass
    
    else:
        try:
            subprocess.check_output(['./judgeClangTool/clangjudge', sub_info[4],
                                'submissions/submission_{}{}'.format(sub_info[2], sub_info[3])])
        except subprocess.CalledProcessError as e:
            error_msg = str(e.output.decode('utf-8'))
            clangtool_log_file = 'sub_clangjudge_{}.log'.format(sub_info[2])
            with open('tmp/' + clangtool_log_file, "w") as log_file:
                log_file.write(error_msg)
            clangjudge_flag = 1
            with open(args.submission_config, "a") as stat_file:
                log_file_name = 'sub_run_{}_{}.log'.format(sub_info[2], sub_info[7])

                with open('tmp/' + log_file_name, "w") as log_file:
                    log_file.write("Clang Checks failed. Program uses function that is not allowed.")

                stat_file.write("{} {} 0 0 {}\n".format(sub_info[7], 'CE2', log_file_name))
                for testcase_id in sub_info[8:]:
                    stat_file.write("{}\n".format(testcase_id))

# First compile
if clangjudge_flag == 0:
    try:
        subprocess.check_output(['./main_compiler.sh', sub_info[0],
                                'submission_{}{}'.format(sub_info[2], sub_info[3])],
                                stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:  # If compilation fails, end this script here
        if isFileBinary or e.returncode == 2:
            error_msg = "Submitted file has invalid format."
            verdict_type = 'CE1'
        else:
            error_msg = str(e.output.decode('utf-8'))
            verdict_type = 'CE0'

        with open(args.submission_config, "a") as stat_file:
            log_file_name = 'sub_run_{}_{}.log'.format(sub_info[2], sub_info[7])

            with open('tmp/' + log_file_name, "w") as log_file:
                log_file.write(error_msg)

            stat_file.write("{} {} 0 0 {}\n"
                            .format(sub_info[7], verdict_type, log_file_name))
            for testcase_id in sub_info[8:]:
                stat_file.write("{}\n".format(testcase_id))
    else:
        subprocess.call(['./main_tester.sh'] + sub_info[0:3] + sub_info[5:])  # run tests
