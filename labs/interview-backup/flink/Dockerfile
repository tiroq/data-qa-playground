# Version-aligned official Flink Kafka SQL connector; demo only.
FROM flink:1.20.3-scala_2.12
USER root
RUN wget -q --tries=3 -O /opt/flink/lib/flink-sql-connector-kafka-3.4.0-1.20.jar \
  https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.4.0-1.20/flink-sql-connector-kafka-3.4.0-1.20.jar \
  && test -s /opt/flink/lib/flink-sql-connector-kafka-3.4.0-1.20.jar
USER flink
