#!/bin/bash

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

pyenv activate hiring

for job in Backend Frontend Tester; do
    python hubspot_resume_mover.py ${job}
done

