docker build -f Dockerfile/Dockerfile . -t canembed/cstylecheck:latest
docker push canembed/cstylecheck:latest
docker run -t -v %cd%:/data -w /data canembed/cstylecheck:latest --version

