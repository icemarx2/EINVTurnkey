#!/bin/bash

javaexec="./jre/bin"
if [[ -n "$JAVA_HOME" && -f "./javahome" ]]; then
    javaexec="$JAVA_HOME/bin"
fi

for n in `ls -1 lib`; do
	if [ -z "$CLASSPATH" ]; then
        CLASSPATH="lib/$n"
    else
        CLASSPATH="$CLASSPATH:lib/$n"
    fi
done

if echo | sort -V >/dev/null 2>&1; then
    SORT_CMD="sort -V"
else
    SORT_CMD="sort"
fi

DOM4_JAR=$(find modules/ -maxdepth 1 -name "dom4j-*.jar" | $SORT_CMD | tail -1)
BCPR_JAR=$(find modules/ -maxdepth 1 -name "bcprov-jdk18on-*.jar" | $SORT_CMD | tail -1)

$javaexec/java -classpath "$CLASSPATH:$DOM4_JAR:$BCPR_JAR" gov.nat.einvoice.tky.alterEncrypt.AlterEncryption