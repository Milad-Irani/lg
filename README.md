# Clip Generator project

clip generator construct of following services:
1.a worker that is the main part of the project . this worker picks up jobs with status Scheduled (SCHED) and complete them. 
2.a server that you could interact with that , create , remove , queue and cancel them. also its a very very versatile tool to monitor your jobs status and created clips. (i will talk about that after)

All above services are availble as docker containers so dont worry about dependencies.

How to start:
excecute Unix shell script `run.sh` .
after that go to http://localhost:8000 , create a job with a video url , create two pointers with values larger than 5. then change job status to Scheduled. Watch logs and Clip model.
as  time goes by , clips will generated. 


# glasoory:
* job: a job is a entity that points to a video that shoudl be downloaded and trimed at some points (called pointers).
* pointer: points on video file that triming eccures before and after them.
* clip: a clip is a entity that involves trimed videos urls . every clip points to a job and a pointer.
* job status: jobs have such status: UnProcessed , Scheduled , UnderProcess , Finished and  Canceled.
