# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Install git
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# Clone the xl2times repository
RUN git clone https://github.com/etsap-TIMES/xl2times.git

# Change to the xl2times directory
WORKDIR /usr/src/app/xl2times

# Install the xl2times package
RUN pip install .

# Set the working directory to the previous WORKDIR
WORKDIR /usr/src/app

# Run times-excel-reader when the container launches
CMD ["xl2times", "TIMES-NZ/", "--output_dir", "TIMES-NZ/raw_table_summary/", "--only_read"]