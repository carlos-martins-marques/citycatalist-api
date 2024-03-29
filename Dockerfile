## Copyright (c) 2015 SONATA-NFV, 2017 5GTANGO [, ANY ADDITIONAL AFFILIATION]
## ALL RIGHTS RESERVED.
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
##
## Neither the name of the SONATA-NFV, 5GTANGO [, ANY ADDITIONAL AFFILIATION]
## nor the names of its contributors may be used to endorse or promote
## products derived from this software without specific prior written
## permission.
##
## This work has been performed in the framework of the SONATA project,
## funded by the European Commission under Grant number 671517 through
## the Horizon 2020 and 5G-PPP programmes. The authors would like to
## acknowledge the contributions of their colleagues of the SONATA
## partner consortium (www.sonata-nfv.eu).
##
## This work has been performed in the framework of the 5GTANGO project,
## funded by the European Commission under Grant number 761493 through
## the Horizon 2020 and 5G-PPP programmes. The authors would like to
## acknowledge the contributions of their colleagues of the 5GTANGO
## partner consortium (www.5gtango.eu).


FROM python:3.5-slim
LABEL organization=5GTANGO

# configurations
ENV CITYCATALIST_API_PORT 8090
ENV USE_SONATA True

ENV SONATA_GTK_COMMON tng-gtk-common
ENV SONATA_GTK_COMMON_PORT 5000
ENV SONATA_GTK_SP tng-gtk-sp
ENV SONATA_GTK_SP_PORT 5000
ENV SONATA_REP tng-rep
ENV SONATA_REP_PORT 4012
ENV SONATA_CAT tng-cat
ENV SONATA_CAT_PORT 4011
ENV SONATA_API tng-api-gtw
ENV SONATA_API_PORT 5000

#Preparing directory
ADD . /citycatalist_api
WORKDIR /citycatalist_api

#runing the python script to prepare the docker environment
RUN apt update
RUN apt -y install gcc
RUN apt -y install libffi-dev
RUN pip3 install paramiko
RUN python setup.py install

#starting the slice-server/service
CMD ["python", "main.py"]
