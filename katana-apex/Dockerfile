FROM nexus3.onap.org:10003/onap/policy-apex-pdp:2.6-SNAPSHOT-latest
WORKDIR /home/apexuser

COPY policy-apex/* /policy-apex/
RUN mkdir -p /policy-json

COPY policy-json/* /policy-json/
COPY logic/* /logic/
COPY config/* /config/
COPY logs/logback.xml /opt/app/policy/apex-pdp/etc/
COPY tosca-template/* /tosca-template/

COPY scripts/* /

EXPOSE 12345 18989 23324 8080 5000

RUN apexCLIToscaEditor.sh -c policy-apex/Policy.apex -ot policy-json/Policy.json -l ./test.log -ac config/config.json -t ./tosca-template/ToscaTemplate.json
CMD ["./start.sh"]

#CMD ["./startTest.sh"]
