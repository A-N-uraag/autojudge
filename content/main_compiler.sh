#!/bin/sh

####################################################
# Using this script
#   ./main_compiler.sh $PROB_CODE $SUB_FILE
# where
# - $PROB_CODE is the problem code of the problem
# - $SUB_FILE is the file that is submitted
####################################################


# All Error Codes pertaining to Compilation
SUCCESS=0
FAILURE=1
FORMAT_FAIL=2

SUB_FDR="submissions"
PROB_FDR="problems"

PROB_CODE=$1
SUB_FILE=$2

. ${PROB_FDR}/${PROB_CODE}/compilation_script.sh

# Now perform string-matching to get the extension
# and the corresponding "executable"
SUBPATH=${SUB_FDR}/${SUB_FILE}
EXECPATH=${SUBPATH%.*}

if ! file --mime -b ${SUBPATH} | grep -i -q "ascii" ; then  # checking for ASCII source files
    return $FORMAT_FAIL
fi

case "$SUBPATH" in
    *.c)
        if ! file --mime -b ${SUBPATH} | grep -i -q "x-c;" ; then  # checking for C source files
            return $FORMAT_FAIL
        fi
        EXTENSION=".c"
        compile_c $SUBPATH $EXECPATH
        if [ -e $EXECPATH ] ; then
	chmod 550 $EXECPATH
	else #This denotes execpath does not exist hence compilation failed!
		$(exit 1) 	
        fi
        ;;
    *.cpp)
        if ! file --mime -b ${SUBPATH} | grep -i -q "x-c++;" ; then  # checking for C++ source files
            return $FORMAT_FAIL
        fi
        EXTENSION=".cpp"
        compile_cpp $SUBPATH $EXECPATH
        if [ -e $EXECPATH ] ; then
	chmod 550 $EXECPATH
	else #This denotes execpath does not exist hence compilation failed!
		$(exit 1) 	
        fi
        ;;
    *.py)
        #TODO: Check for Python file
        EXTENSION=".py"
        compile_py $SUBPATH $EXECPATH
        if [ -e $EXECPATH ] ; then
	chmod 550 $EXECPATH
	else #This denotes execpath does not exist hence compilation failed!
		$(exit 1) 	
        fi
        ;;
    *.go)
        #TODO: Check for Go file
        EXTENSION=".go"
        compile_go $SUBPATH $EXECPATH
        if [ -e $EXECPATH ] ; then
	chmod 550 $EXECPATH
	else #This denotes execpath does not exist hence compilation failed!
		$(exit 1) 	
        fi
        ;;
    *.hs)
        #TODO: Check for Haskell file
        EXTENSION=".hs"
        compile_hs $SUBPATH $EXECPATH
        if [ -e $EXECPATH ] ; then
	chmod 550 $EXECPATH
	else #This denotes execpath does not exist hence compilation failed!
		$(exit 1) 	
        fi
        ;;
    *)
        EXTENSION=".none"
        ;;
esac

# Return the status of compilation
return $?
