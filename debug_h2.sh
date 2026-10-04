#!/bin/bash

cd "$(dirname "$0")"

javaexec="java"
if [[ -d "./jre/bin" ]]; then
    javaexec="./jre/bin/java"
fi
if [[ -n "$JAVA_HOME" && -f "./javahome" ]]; then
    javaexec="$JAVA_HOME/bin/java"
fi

for n in `ls -1 modules`; do
    MODULEPATH=$MODULEPATH:modules/$n
done

for n in `ls -1 lib`; do
	if [ -z "$CLASSPATH" ]; then
        CLASSPATH=lib/$n
    else
        CLASSPATH=$CLASSPATH:lib/$n
    fi
done

echo "Java Exec: $javaexec"
echo "Running H2 Check..."
$javaexec -classpath $CLASSPATH:modules/dom4j-2.1.3.jar:modules/bcprov-jdk18on-1.76.jar gov.nat.einvoice.tky.alterEncrypt.UpDateH2Version
EXIT_CODE=$?
echo "H2 Check finished with exit code: $EXIT_CODE"
