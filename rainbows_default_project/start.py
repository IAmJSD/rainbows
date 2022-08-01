#!/usr/bin/env python

# This file just calls the run function. Whilst you could do other stuff here, it's super unintended and will make help
# harder. Please don't!

import rainbows.bootstrap
import ntpath

if __name__ == "__main__":
    rainbows.bootstrap.run(ntpath.dirname(__file__))
