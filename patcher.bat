if exist %1 (
    bin/wit extract -s vanilla -D tmp -o
    python3 patcher.py %1
    bin/wit copy tmp -o %~n1.wbfs
    rd /s /q tmp
) else (
    echo "No patch file specified. Aborting."
    pause
)