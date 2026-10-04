#!/bin/bash

cd "$(dirname "$0")"

javaexec="java"
if [[ -d "./jre/bin" ]]; then
    javaexec="./jre/bin/java"
fi
if [[ -n "$JAVA_HOME" && -f "./javahome" ]]; then
    javaexec="$JAVA_HOME/bin/java"
fi

if test -f "EINVUPGRADE/upgrade.sh"; then
    `./EINVUPGRADE/upgrade.sh`
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

$javaexec --module-path $MODULEPATH --add-modules gov.nat.einvoicetky -classpath $CLASSPATH --module gov.nat.einvoicetky/gov.nat.einvoice.tky.TurnkeyCmd start-monitor