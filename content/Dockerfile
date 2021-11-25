# Official Ubuntu 20.04
FROM ubuntu:20.04

ARG DEBIAN_FRONTEND="noninteractive"

### LANGUAGE SUPPORT BELOW
### Currently we support C, C++, Python3.8, Java, Go and Haskell

# Install basic dependencies
# Installing build-essential installs gcc-9 and g++-9 for C / C++ and
# Installing software-properties-common installs python3.8 for Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    apt-utils \
    build-essential \
    make \
    curl \
    wget \
    git \
    file \
    ca-certificates \
    software-properties-common && \
    rm -rf /var/lib/apt/lists/*

# Install golang for Go
RUN apt-get update && apt-get install -y --no-install-recommends \
    golang && \
    rm -rf /var/lib/apt/lists/*

# Set the PATH variables after golang install
ENV GOPATH=${HOME}/go
ENV PATH=${PATH}:${GOPATH}/bin

# Install ghc for Haskell
RUN add-apt-repository -y ppa:hvr/ghc && \
    apt-get update && apt-get install -y --no-install-recommends \
    ghc-8.6.5 && \
    rm -rf /var/lib/apt/lists/*

# Set the PATH variables after ghc install
ENV PATH=${PATH}:/opt/ghc/bin

### TIMER_TOOL SUPPORT BELOW

# Install dependencies for timer_tool (a.k.a. runsolver)
RUN apt-get update && apt-get install -y libnuma-dev && \
    rm -rf /var/lib/apt/lists/* 

# Install timer_tool (a.k.a. runsolver)
RUN git clone --branch ITP https://github.com/anilavakundu/runsolver.git ~/runsolver && \
    sed -i 's/include/-include/g' ~/runsolver/src/Makefile && \
    make -C ~/runsolver/src runsolver && \
    mv ~/runsolver/src/runsolver ~/timer_tool && \
    rm -r ~/runsolver/ && \
    mv ~/timer_tool /bin/timer_tool

# Set local timezone to UTC+5:30
RUN apt-get update && \
    apt-get install -yq tzdata && \
    ln -fs /usr/share/zoneinfo/Asia/Kolkata /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

# Submission ID, to be set at runtime in `docker run` calls
ENV SUB_ID=-1

# Set working directory
WORKDIR /app

# Run the meta script
CMD python3.8 compile_and_test.py --submission_config tmp/sub_run_${SUB_ID}.txt
