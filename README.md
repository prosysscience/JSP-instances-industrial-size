# JSP-instances-industrial-size

Here we extend our initial work (https://github.com/prosysscience/Job-Shop-Scheduling) on a job-shop scheduling problem of a large size using of Answer Set Programming (ASP) modulo difference logic:

The number of jobs and machines is 100, and the total number of operations to be scheduled is 10000. The model splits the problem into sub-problems where the operations are assigned to a specific time window while respecting the precedence constraints. 

- The decomposition depends on ranking the operations based on the Earliest Starting Time (EST) and inserting the operation, which is processed by the most bottleneck machine, to an earlier time window.

- The available instances are split into 30-time windows because it provides better results

- The main objective is to minimize the total makespan

- The model is controlled using a Python script, which is responsible for optimizing the time windows

This repository includes the following files/folders:

<table>
<tr><th>File/Folder</th><th>Description</th></tr>
<tr><td style="font-family:'Courier New'">README.md</td><td>this file</td></tr>
<tr><td style="font-family:'Courier New'">encoding.lp</td><td>scheduling encoding in ASP modulo difference logic</td></tr>
<tr><td style="font-family:'Courier New'">instances</td><td>instance files for testing</td></tr>
<tr><td style="font-family:'Courier New'">main.py</td><td>Python script to run multi-shot ASP solving for optimization</td></tr>
</table>

## Usage

The script for running our scheduling encoding and instances relies on the Python (3.9.18) libraries of [Clingo] (https://potassco.org/clingo/) (5.6.2) and [Clingo[DL]] (https://potassco.org/labs/clingodl/) (1.4.0). The following example call illustrates run, with time limits of 21600 seconds (6 hours) for makespan minimization.


- :
    - ``./main.py encoding.lp instances/tai_j100_m100_1.lp ``
    - ``...``
    - ``./main.py encoding.lp instances/tai_j100_m100_10.lp ``

