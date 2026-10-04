#!/bin/bash

javaexec="./jre/bin"
if [[ -n "$JAVA_HOME" && -f "./javahome" ]]; then
    javaexec="$JAVA_HOME/bin"
fi

if test -f "EINVUPGRADE/upgrade.sh"; then
    `./EINVUPGRADE/upgrade.sh`
    echo 'Upgrade end Restart...'
    ./run_cmd.sh
    exit 0
fi

for n in `ls -1 modules`; do
    MODULEPATH="$MODULEPATH:modules/$n"
done

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

if [ "`uname -m`" = "x86_64" ]; then
    export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:so/x64"
else
    export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:so/x86"
fi

echo 'CHK H2 ....'
$javaexec/java -classpath "$CLASSPATH:$DOM4_JAR:$BCPR_JAR" gov.nat.einvoice.tky.alterEncrypt.UpDateH2Version

echo 'TKY starting ....'
$javaexec/java --module-path $MODULEPATH --add-modules gov.nat.einvoicetky -classpath $CLASSPATH --module gov.nat.einvoicetky/gov.nat.einvoice.tky.TurnkeyCmd interactive
