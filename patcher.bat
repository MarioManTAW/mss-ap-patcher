if exist %1 (
    %~dp0\bin\wit.exe extract -s vanilla -D tmp -o || pause
    python3 patcher.py %1 || pause
    %~dp0\bin\wit.exe copy tmp -o %~n1.wbfs || pause
    rd /s /q tmp
) else (
    echo "No patch file specified. Aborting."
    pause
)