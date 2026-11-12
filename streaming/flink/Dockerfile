# Flink 1.20 uses the matching Apache Kafka SQL connector 3.4.0-1.20.
# The SQL connector includes its runtime dependencies; do not add the thin
# flink-connector-kafka jar as well (it can cause classpath collisions).
FROM flink:1.20.3
USER root
ADD https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.4.0-1.20/flink-sql-connector-kafka-3.4.0-1.20.jar /opt/flink/lib/flink-sql-connector-kafka-3.4.0-1.20.jar
RUN test -s /opt/flink/lib/flink-sql-connector-kafka-3.4.0-1.20.jar && chmod 0644 /opt/flink/lib/flink-sql-connector-kafka-3.4.0-1.20.jar
USER flink
