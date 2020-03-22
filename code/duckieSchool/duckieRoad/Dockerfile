# Definition of data download and extraction container
# We start from a ros image
FROM ros:kinetic-ros-base-xenial

# DO NOT MODIFY
RUN apt-get update -y && apt-get install -y --no-install-recommends \
         gcc \
         libc-dev\
         git \
         htop \
         python-pip \
         bzip2 \
         python-tk && \
     rm -rf /var/lib/apt/lists/*

# let's create our workspace, we don't want to clutter the container
# RUN mkdir /workspace

RUN apt-get update

# Required for python to find rosbag package
ENV PYTHONPATH="/opt/ros/kinetic/lib/python2.7/dist-packages/:${PYTHONPATH}"

RUN apt-get install -y ros-kinetic-cv-bridge
RUN apt-get update

# we make the workspace our working directory
WORKDIR /workspace
# if you have more file use the COPY command to move them to the workspace
# Unnecessary files are ignored using .dockerignore file
COPY . .

# here, we install the requirements, some requirements come by default
# you can add more if you need to in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install dependencies
RUN mkdir /workspace/data

RUN mkdir /workspace/data/bag_files

COPY bag_files/ /workspace/data/bag_files


#COPY avlduck3_2019-12-10-15-55-53.bag /workspace/data/bag_files/
#COPY avlduck3_2019-12-10-15-58-41.bag /workspace/data/bag_files/

# Extract data into useable format
RUN python2 src/extract_data.py

RUN tail -f /dev/null