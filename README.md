Serverless Face Recognition
---

### Description:

ADD SOMETHING

See our [blog post](BLOG.md) for a detailed description of the system and
the machine learning methods that underpin this work. And if this work
sparks new ideas or influences your research, please cite us (see below)!

### Setup:

```bash
# install dependencies
>$ sudo apt-get install python-pip

>$ git clone https://github.com/excamera/serverless-face-recognition.git
>$ cd serverless-face-recognition
>$ sudo pip install -r requirements.txt

# setup the awscli (create an access key and enter details below)
>$ aws configure
AWS Access Key ID []: ****************ANWQ
AWS Secret Access Key []: ****************JawS
Default region name []: us-east-1
Default output format [None]:

# deploy our face recognition code to your account
>$ ./install_lambdas.sh
creating bucket
uploading dependencies to s3
upload: blobs/deps.zip to s3://9a480eb7-be5b-4e15-81fe-4de41323907e/deps.zip
upload: blobs/root-495M-2017-02-06.tar.gz to s3://9a480eb7-be5b-4e15-81fe-4de41323907e/root-495M-2017-02-06.tar.gz
upload: blobs/lfw_face_vectors.csv.gz to s3://9a480eb7-be5b-4e15-81fe-4de41323907e/lfw_face_vectors.csv.gz
adding 'lambda-executor' role
adding 'prepare-face-recognizer' lambda
adding 'recognize-face' lambda
Done!
```

### Usage:

```bash
# generating a model for a face
>$ ./train_face_recognizer.py
description:
    returns the augmented feature vectors for the face in IMAGE.csv.
            Assume exactly one face in the image

# using a model to recognize a face in an image
>$ ./recognize_face.py
usage: ./recognize_face.py FACEVECTORS.csv IMAGE.jpg
description:
    returns `true` or `false` if the face used to generate
            FACEVECTORS.csv is present in IMAGE.csv
            ```

### Example:

To see how things work let's jump into a simple example. The following snippet will train the face recognizer on [John Emmons'](http://johnemmons.com) face then use
the model to check if John's face is in some of the example photos.

```bash
# generate a model for John's face
>$ cd scripts
>$ ./train_face_recognizer.py pics/john0.jpg > john.model.csv

# use the model to see if John's face is present in an image
>$ ./recognize_face.py john.model.csv pics/john1.jpg
True

>$ ./recognize_face.py john.model.csv pics/john2.jpg
True

>$ ./recognize_face.py john.model.csv pics/jim-carrey.jpg
False
```


### About Us:

My name is [John Emmons](http://johnemmons.com) and I am a computer science PhD student at Stanford University. I solve problems at the intersection of computer systems and machine learning (especially computer vision).

If you like the work and want to talk me, feel free to drop me a line a [mail@johnemmons.com](mailto:mail@johnemmons.com). And if this work inspires you to do your own related work, please cite me and my research group's work!

### Citation:

```
@inproceedings {201559,
  author = {Sadjad Fouladi and Riad S. Wahby and Brennan Shacklett and Karthikeyan Vasuki Balasubramaniam and William Zeng and Rahul Bhalerao and Anirudh Sivaraman and George Porter and Keith Winstein},
  title = {Encoding, Fast and Slow: Low-Latency Video Processing Using Thousands of Tiny Threads},
  booktitle = {14th USENIX Symposium on Networked Systems Design and Implementation (NSDI 17)},
  year = {2017},
  isbn = {978-1-931971-37-9},
  address = {Boston, MA},
  pages = {363--376},
  url = {https://www.usenix.org/conference/nsdi17/technical-sessions/presentation/fouladi},
  publisher = {USENIX Association},
 }
 ```   