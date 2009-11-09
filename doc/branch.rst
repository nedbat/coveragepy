Coverage.py now supports branch coverage

- How to use it.

- Reporting

- How it works

- Odd cases

    - yellow-pink syndrome:
    
        Y       if never_true:
        P           never_executed()
    
    - while True is marked as yellow

    - except ValueError will be marked as yellow if you never see a different exception.
    
- Exceptions?

    - What should we do with the info about unpredicted arcs?

- Excluding. Does it work?
