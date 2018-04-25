import bluesky as bs
import bluesky.plans as bp

## vortex_me4.count_mode.put(0)               put the Struck in OneCount mode (1 is AutoCount)
## vortex_me4.preset_time.put(0.5)            set the OneCount accumulation time
## vortex_me4.auto_count_time.put(0.5)        set the AutoCount accumulation time
## vortex_me4.count.put(1)                    trigger a OneCount
## ... then can get the channel values

## quadem1.acquire_mode.put(0)                Continuous acquire mode
## quadem1.acquire_mode.put(1)                Multiple acquire mode
## quadem1.acquire_mode.put(2)                Single acquire mode
## quadem1.acquire.put(1)                     trigger acquisition in any of the modes
## ... then can get the channel values

## -----------------------
##  energy scan plan concept
##  1. collect metadata from an INI file
##  2. compute scan grid
##  3. move to center of angular range
##  4. drop into pseudo channel cut mode
##  5. set OneCount and Single modes on the detectors
##  6. begin scan repititions, for each one
##     a. set acquisition times
##     b. move
##     c. trigger
##     d. collect
##     e. grab dataframe from Mongo
##     f. write XDI file
##  8. return to fixed exit mode
##  9. return detectors to AutoCount and Continuous modes
