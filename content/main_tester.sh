#!/bin/sh

#############################################################################
# Using this script
#    ./main_tester.sh $PROB_CODE $SUB_ID $TIMELIMIT $MEMLIMIT [$TESTCASE_ID]+
# where
# - $PROB_CODE is the problem code
# - $SUB_ID is the submission ID
# - $TIMELIMIT is the time limit
# - $MEMLIMIT is the memory limit
# - $TESTCASE_ID is the testcase ID (pass atleast 1)
#############################################################################

# All Error Codes pertaining to Testing
PASS=0
FAIL=1
TLE=2
OOM=3
RE=4
NA=5

# Assume a directory structure
# content/
# ├── problems/
# ├── submissions/
# ├── testcase/
# ├── tmp/
# ├── compile_and_test.py
# ├── main_compiler.sh
# ├── main_tester.sh
# └── Dockerfile

PROB_FDR="problems"
SUB_FDR="submissions"
TEST_FDR="testcase"
INPUT_FDR="inputs"
TMP="tmp"

# Problem code
PROB_CODE=$1
shift

# Pass command line arguments
IS_CMDLINE=$1
shift

# Submission ID
SUB_ID=$1
shift

# Time Limit
TIMELIMIT=$1
shift

# Memory Limit
MEMLIMIT=$1
shift

# Run submission function
# If the executable runs fine, then the output validation is done
# Otherwise, an appropriate error code is returned
run_submission() {
  SID=$1
  TID=$2
  TLIMIT=$3
  MLIMIT=$4
  CMDARGS=$5
  
  #A flag to denote any limit was exceeded
  LIMITFLAG=0
  TimeLimit=0
  fileSizePanic=0
  VERDICT=""
  
  # This is what we do:
  # - Run the timer_tool wrapped with the timeout tool, and then we send this process in the background
  #	- We poll the background process to check if it is alive while doing so we also check the output file size
  #     - If output file size exceeds limit [> 100KB for now] kill process and we show appropriate message
  # 	- if file size is not exceeding we follow with timeout and memout checks
  #     - If no, return the appropriate errors
  #     - If yes, re-run again to get the final submission output
  #       This is then checked normally using a diff
  #       The status is appended to the verdict_string along with the memory and time consumed

  if [ "$CMDARGS" = 0 ] ; then
  
		# Wrapping timer_tool(runsolver) with timeout tool as timeout tool support seconds below 0(0.001s) 
		# For runsolver first two lines specify the flags required
		# -w /dev/null pipes output of the tool to /dev/null, --vsize-limit gives the virtual size limit
		# --cores 0 limits to only one core,
		# --var provides a file with specific flags which are used for checking
		# Can use --input, -o flags instead of redirection
		# The last line runs the process
		timeout -s 15 $TLIMIT timer_tool -w /dev/null --vsize-limit $MLIMIT --cores 0 \
						--var ${TMP}/submission_status_${SID}_${TID}.txt \
						${INPUT_FDR}/submission_${SID} < ${TEST_FDR}/inputfile_${TID}.txt > ${TMP}/sub_output_${SID}_${TID}.txt 2> ${TMP}/sub_run_${SID}_${TID}.log & #Run this in background
		limit_proc_id=$! #Getting PID of background process
		
		wasNotFound=0 #Setting flag to poll background process

		#Polling background process
		#Can use --output-limit flag of timer_tool
		#But this is faster as it terminates as soon as size limit is reached
		while [ "$wasNotFound" != 1 ] 
		do
			ps | grep -q "$limit_proc_id"
			wasNotFound=$?
			if [ -f ${TMP}/sub_output_${SID}_${TID}.txt ]; then
				fileSize=$(wc -c < "${TMP}/sub_output_${SID}_${TID}.txt")
				if [ "$fileSize" -ge 102400 ] ; then #checking if file size is more than 100 KB
					fileSizePanic=1
					kill $limit_proc_id
					break
				fi
			fi
		done 

		#If we panicked with file size checks we output message 
		if [ "$fileSizePanic" = 1 ] ; then
			VERDICT=$(error_code_to_string $RE ${TID})
			echo "Output Text limit exceeded!" > ${TMP}/sub_run_${SID}_${TID}.log
			LIMITFLAG=1
		fi 

		wait $limit_proc_id #This is blocking call and waits for the background process to end

			
		# We get the exit status of the background process and check if the submission timed out
		if [ "$?" = 124 ] ; then
		
			# Remove the log file generated from runsolver
				rm ${TMP}/submission_status_${SID}_${TID}.txt

			VERDICT=$(error_code_to_string $TLE ${TID})
			echo "Time limit exceeded" > ${TMP}/sub_run_${SID}_${TID}.log
			TimeLimit=1
			LIMITFLAG=1
		
		# Else we check for MLE
		else
			# Make all the flags as env vars for checking and remove this file
			. ${TMP}/submission_status_${SID}_${TID}.txt
			rm ${TMP}/submission_status_${SID}_${TID}.txt
		
			#Checking if it is MLE 
			if [ "$MEMOUT" = true ] ; then
				VERDICT=$(error_code_to_string $OOM ${TID})
				echo "Memory limit exceeded" > ${TMP}/sub_run_${SID}_${TID}.log
				LIMITFLAG=1	
			fi
			
		fi
	else 

		lines=$(cat ${TEST_FDR}/inputfile_${TID}.txt | wc -l)
		for n in $(seq $lines); do

			#echo $(sed "${n}q;d" $input_file)

			timeout -s 15 $TLIMIT timer_tool -w /dev/null --vsize-limit $MLIMIT --cores 0 \
						--var ${TMP}/submission_status_${SID}_${TID}.txt \
						${INPUT_FDR}/submission_${SID} $(sed "${n}q;d" ${TEST_FDR}/inputfile_${TID}.txt) >> ${TMP}/sub_output_${SID}_${TID}.txt 2>> ${TMP}/sub_run_${SID}_${TID}.log & #Run this in background


			limit_proc_id=$! #Getting PID of background process

			wasNotFound=0 #Setting flag to poll background process

			#Polling background process
			#Can use --output-limit flag of timer_tool
			#But this is faster as it terminates as soon as size limit is reached
			while [ "$wasNotFound" != 1 ]
			do
			   ps | grep -q "$limit_proc_id"
			   wasNotFound=$?
			   if [ -f ${TMP}/sub_output_${SID}_${TID}.txt ]; then
				fileSize=$(wc -c < "${TMP}/sub_output_${SID}_${TID}.txt")
				if [ "$fileSize" -ge 102400 ] ; then #checking if file size is more than 100 KB
					fileSizePanic=1
					kill $limit_proc_id
					break
				fi
			   fi


			done

			if [ "$fileSizePanic" = 1 ] ; then
			    VERDICT=$(error_code_to_string $RE ${TID})
			    echo "Output Text limit exceeded!" > ${TMP}/sub_run_${SID}_${TID}.log
			    LIMITFLAG=1
			    # break
			fi


			wait $limit_proc_id #This is blocking call and waits for the background process to end

			if [ "$fileSizePanic" = 1 ] ; then
				# Remove the log file generated from runsolver
				rm ${TMP}/submission_status_${SID}_${TID}.txt
				break
			fi

			# We get the exit status of the background process and check if the submission timed out
			if [ "$?" = 124 ] ; then

			    # Remove the log file generated from runsolver
			    rm ${TMP}/submission_status_${SID}_${TID}.txt

			    VERDICT=$(error_code_to_string $TLE ${TID})
			    echo "Time limit exceeded" > ${TMP}/sub_run_${SID}_${TID}.log
			    TimeLimit=1
			    LIMITFLAG=1
			    break


			else
			     # Make all the flags as env vars for checking and remove this file
			     . ${TMP}/submission_status_${SID}_${TID}.txt
			     rm ${TMP}/submission_status_${SID}_${TID}.txt
		
			     #Checking if it is MLE 
			     if [ "$MEMOUT" = true ] ; then
			         VERDICT=$(error_code_to_string $OOM ${TID})
			         echo "Memory limit exceeded" > ${TMP}/sub_run_${SID}_${TID}.log
			         LIMITFLAG=1
			 	 break	 
			     fi


			fi
		 done
	fi
       
    
  #If no limit was exceeded normal flow resumes
  if [ "$LIMITFLAG" = 0 ] ; then
    case "$EXITSTATUS" in
      "0")
          fileSize=$(wc -c < "${TMP}/sub_output_${SID}_${TID}.txt")
          if [ "$fileSize" -le 1 ] ; then
            echo -n " " >> ${TMP}/sub_output_${SID}_${TID}.txt
          fi
          if ! file --mime -b ${TMP}/sub_output_${SID}_${TID}.txt | grep -i -q "ascii" ; then  # checking for ASCII output file
            echo "Output has invalid text" > ${TMP}/sub_run_${SID}_${TID}.log
            VERDICT=$(error_code_to_string $RE ${TID})
          else
            ./${PROB_FDR}/${PROB_CODE}/test_script ${TEST_FDR}/outputfile_${TID}.txt ${TMP}/sub_output_${SID}_${TID}.txt > /dev/null
            VERDICT=$(error_code_to_string $? ${TID})
          fi
          ;;
      *)
          echo "\nExit code: $EXITSTATUS" >> ${TMP}/sub_run_${SID}_${TID}.log
          VERDICT=$(error_code_to_string $RE ${TID})
          ;;
    esac
  fi
  
  if ! [ -s ${TMP}/sub_run_${SID}_${TID}.log ] ; then #if error stream is empty take the output. Will later be used to show difference of output if testcase has failed
     cat ${TMP}/sub_output_${SID}_${TID}.txt > ${TMP}/sub_run_${SID}_${TID}.log
  fi


  if [ "$TimeLimit" = 1 ] ; then
	VERDICT="${VERDICT} 0 0 sub_run_${SID}_${TID}.log"
  else
  	VERDICT="${VERDICT} ${WCTIME} ${MAXVM} sub_run_${SID}_${TID}.log"
  fi
  echo ${VERDICT}
}

clean_generated_output() {
  rm ${TMP}/sub_output_${1}_${2}.txt
  mv ${INPUT_FDR}/submission_${SUB_ID} .
  rm -rf ${INPUT_FDR}/*
  mv submission_${SUB_ID} ${INPUT_FDR}
}


# Convert error code to character string
error_code_to_string() {
  ERRCODE=$1
  TID=$2

  case "$ERRCODE" in
    "$PASS")
        STRCODE="P"
        ;;
    "$FAIL")
        STRCODE="F"
        ;;
    "$TLE")
        STRCODE="TE"
        ;;
    "$OOM")
        STRCODE="ME"
        ;;
    "$CE")
        STRCODE="CE"
        ;;
    "$RE")
        STRCODE="RE"
        ;;
    "$NA")
        STRCODE="NA"
        ;;
    *)
        STRCODE="NA"
        ;;
  esac

  echo "$TESTCASE_ID $STRCODE"
}

# Add executable permission
chmod ug+x ${PROB_FDR}/${PROB_CODE}/test_script

mkdir ${INPUT_FDR}
mv ${SUB_FDR}/submission_${SUB_ID} ${INPUT_FDR}

# Check for input files
HAS_INPUT_FILES=0
if [ -f ${PROB_FDR}/${PROB_CODE}/input_files.zip ]; then
	if file --mime -b ${PROB_FDR}/${PROB_CODE}/input_files.zip | grep -i -q "application/zip" ; then
		HAS_INPUT_FILES=1
	fi
fi

# Iterate over all testcase IDs passed as command line arguments
for TESTCASE_ID in "$@";
  do
	# Extract input_files.zip to ./inputs/
	if [ "$HAS_INPUT_FILES" = 1 ]; then
		unzip ${PROB_FDR}/${PROB_CODE}/input_files.zip -d ${INPUT_FDR}
	fi

    # Run the submission using run_submission
    run_submission ${SUB_ID} ${TESTCASE_ID} ${TIMELIMIT} ${MEMLIMIT} ${IS_CMDLINE} >> ${TMP}/sub_run_${SUB_ID}.txt

    # Remove the generated output files
    clean_generated_output ${SUB_ID} ${TESTCASE_ID}
  done

rm -rf ${INPUT_FDR}
