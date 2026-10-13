# Stock vehicle weather balance

Two laps from a standing start, one AI-driven vehicle at a time, on Peach Pit, Foundry Flats, Launchpad Loop and Dune Drift. All 22 stock vehicles; clear, rain and snow; daytime; random seed 12345 reset before each race. No vehicle or driving changes were made for this run.

Each percentage is the mean of the vehicle's time divided by the median time on each course, minus one. Negative is quicker than the field; positive is slower. The rain/snow change columns subtract the dry percentage: negative means the vehicle gains relative to its peers in that weather. These are percentage-point changes, not raw speed changes.

This is one seed and one two-lap run per combination, using AI. It identifies candidates for follow-up, not a measure of human performance or consistency across all courses and puddle layouts.

## Findings

- Clear: vehicles outside the usual roughly ±10% overall target: none.
- Rain: vehicles outside the usual roughly ±10% overall target: rocket (-12.5%).
- Snow: vehicles outside the usual roughly ±10% overall target: rocket (-14.3%).

Weather-specific outliers should be checked with more seeds before retuning. Changing a vehicle globally to correct a wet-weather advantage may disturb its dry balance.

## Relative pace

| Vehicle | Clear | Rain | Snow | Rain change | Snow change |
| --- | ---: | ---: | ---: | ---: | ---: |
| brick_tank | -5.8% | -8.1% | -7.9% | -2.4 pp | -2.2 pp |
| bruiser | -3.9% | -7.3% | -6.7% | -3.4 pp | -2.7 pp |
| chopper | +1.5% | +2.5% | +3.3% | +1.0 pp | +1.8 pp |
| classic | +0.7% | +1.7% | +2.1% | +1.0 pp | +1.4 pp |
| dirt_bike | +6.7% | +2.6% | +0.3% | -4.1 pp | -6.4 pp |
| downforce | -5.0% | -5.3% | -1.4% | -0.4 pp | +3.6 pp |
| featherlight | +4.1% | +5.4% | +6.4% | +1.3 pp | +2.2 pp |
| hot_rod | +0.8% | +2.3% | +3.4% | +1.5 pp | +2.6 pp |
| monster | +2.4% | -4.4% | -7.1% | -6.9 pp | -9.6 pp |
| mudlark | +0.8% | -4.8% | -7.9% | -5.6 pp | -8.7 pp |
| rocket | -5.6% | -12.5% | -14.3% | -6.9 pp | -8.7 pp |
| scooter | -1.0% | -0.3% | +0.3% | +0.6 pp | +1.2 pp |
| six_wheeler | -4.7% | -3.6% | -2.8% | +1.2 pp | +2.0 pp |
| slingshot | -5.6% | -5.5% | -4.7% | +0.1 pp | +1.0 pp |
| soapbox | +1.2% | +1.6% | +0.6% | +0.4 pp | -0.6 pp |
| sparky | +1.5% | +3.1% | +2.9% | +1.6 pp | +1.4 pp |
| starter | -0.5% | +0.7% | +0.6% | +1.3 pp | +1.1 pp |
| streamliner | -3.4% | -2.0% | -1.8% | +1.4 pp | +1.6 pp |
| superbike | +1.0% | +1.8% | +2.5% | +0.8 pp | +1.5 pp |
| tourer | +4.5% | +5.3% | +5.9% | +0.8 pp | +1.4 pp |
| trike | -5.4% | -4.5% | -3.8% | +0.9 pp | +1.6 pp |
| trikester | +6.1% | +6.5% | +7.0% | +0.4 pp | +1.0 pp |

## Clear

88/88 runs finished; 1 resets in total. Times below are seconds for both laps.

Worker logs: 0 engine errors; 3 Jolt job-capacity warnings during concurrent runs.

| Vehicle | Peach Pit | Foundry Flats | Launchpad Loop | Dune Drift | Resets |
| --- | ---: | ---: | ---: | ---: | ---: |
| Field median | 166.0 | 171.7 | 177.7 | 178.6 | — |
| brick_tank | 158.0 | 161.3 | 168.2 | 166.5 | 0 |
| bruiser | 165.9 | 164.4 | 169.0 | 167.0 | 0 |
| chopper | 165.8 | 176.9 | 179.0 | 182.9 | 0 |
| classic | 168.3 | 170.9 | 180.2 | 179.7 | 0 |
| dirt_bike | 177.4 | 186.4 | 187.0 | 190.0 | 0 |
| downforce | 162.3 | 160.5 | 167.7 | 168.9 | 0 |
| featherlight | 171.1 | 180.4 | 184.1 | 187.1 | 0 |
| hot_rod | 169.8 | 172.6 | 177.3 | 179.9 | 0 |
| monster | 175.2 | 175.2 | 181.4 | 178.8 | 0 |
| mudlark | 167.0 | 174.2 | 180.5 | 177.8 | 0 |
| rocket | 167.2 | 167.2 | 161.2 | 158.3 | 1 |
| scooter | 163.0 | 170.5 | 175.6 | 178.4 | 0 |
| six_wheeler | 156.1 | 163.4 | 169.9 | 171.9 | 0 |
| slingshot | 153.4 | 160.9 | 170.3 | 170.7 | 0 |
| soapbox | 165.6 | 174.1 | 180.8 | 182.2 | 0 |
| sparky | 170.0 | 173.5 | 180.6 | 180.3 | 0 |
| starter | 166.1 | 169.8 | 177.3 | 177.1 | 0 |
| streamliner | 158.8 | 165.4 | 172.7 | 173.8 | 0 |
| superbike | 164.5 | 176.3 | 178.1 | 181.9 | 0 |
| tourer | 174.2 | 180.2 | 183.8 | 186.8 | 0 |
| trike | 159.3 | 161.9 | 166.9 | 168.6 | 0 |
| trikester | 176.2 | 182.8 | 186.9 | 190.4 | 0 |

## Rain

88/88 runs finished; 5 resets in total. Times below are seconds for both laps.

Worker logs: 0 engine errors; 1 Jolt job-capacity warnings during concurrent runs.

| Vehicle | Peach Pit | Foundry Flats | Launchpad Loop | Dune Drift | Resets |
| --- | ---: | ---: | ---: | ---: | ---: |
| Field median | 188.4 | 200.4 | 202.6 | 205.5 | — |
| brick_tank | 172.0 | 180.7 | 189.9 | 189.5 | 0 |
| bruiser | 177.7 | 182.7 | 189.6 | 188.4 | 0 |
| chopper | 193.5 | 205.8 | 206.0 | 211.6 | 0 |
| classic | 194.3 | 201.4 | 206.8 | 207.6 | 0 |
| dirt_bike | 196.1 | 205.3 | 205.7 | 210.5 | 0 |
| downforce | 178.1 | 185.5 | 193.3 | 197.5 | 0 |
| featherlight | 199.2 | 211.0 | 213.1 | 216.5 | 0 |
| hot_rod | 197.6 | 202.2 | 206.2 | 208.7 | 0 |
| monster | 185.5 | 189.8 | 194.2 | 191.7 | 0 |
| mudlark | 179.4 | 189.2 | 195.8 | 194.3 | 0 |
| rocket | 174.6 | 173.9 | 174.7 | 173.1 | 0 |
| scooter | 186.8 | 199.4 | 201.6 | 206.5 | 0 |
| six_wheeler | 181.6 | 191.8 | 195.8 | 199.3 | 0 |
| slingshot | 173.8 | 184.4 | 196.6 | 198.7 | 0 |
| soapbox | 190.0 | 205.0 | 206.5 | 208.3 | 1 |
| sparky | 196.8 | 207.9 | 207.9 | 208.5 | 1 |
| starter | 190.0 | 204.4 | 203.6 | 204.6 | 2 |
| streamliner | 183.9 | 197.1 | 198.8 | 201.3 | 1 |
| superbike | 191.6 | 205.3 | 204.0 | 210.2 | 0 |
| tourer | 202.8 | 209.2 | 211.5 | 215.4 | 0 |
| trike | 185.2 | 188.5 | 192.1 | 195.1 | 0 |
| trikester | 205.0 | 211.6 | 213.5 | 218.1 | 0 |

## Snow

88/88 runs finished; 3 resets in total. Times below are seconds for both laps.

Worker logs: 0 engine errors; 1 Jolt job-capacity warnings during concurrent runs.

| Vehicle | Peach Pit | Foundry Flats | Launchpad Loop | Dune Drift | Resets |
| --- | ---: | ---: | ---: | ---: | ---: |
| Field median | 213.8 | 225.5 | 228.1 | 233.3 | — |
| brick_tank | 194.1 | 206.6 | 213.9 | 214.9 | 0 |
| bruiser | 199.7 | 212.1 | 214.3 | 214.6 | 0 |
| chopper | 222.0 | 233.6 | 233.7 | 241.2 | 0 |
| classic | 221.7 | 226.8 | 234.8 | 236.0 | 0 |
| dirt_bike | 214.8 | 227.2 | 227.9 | 233.6 | 0 |
| downforce | 209.7 | 219.9 | 227.3 | 231.4 | 0 |
| featherlight | 228.3 | 239.9 | 243.1 | 246.7 | 0 |
| hot_rod | 226.2 | 231.2 | 235.4 | 238.5 | 0 |
| monster | 196.9 | 223.9 | 207.9 | 207.6 | 2 |
| mudlark | 195.2 | 207.7 | 212.8 | 213.7 | 0 |
| rocket | 184.6 | 197.3 | 194.8 | 195.1 | 1 |
| scooter | 213.5 | 226.5 | 228.3 | 234.9 | 0 |
| six_wheeler | 207.6 | 219.3 | 221.7 | 227.3 | 0 |
| slingshot | 197.3 | 212.6 | 223.3 | 226.2 | 0 |
| soapbox | 214.2 | 226.2 | 231.7 | 234.1 | 0 |
| sparky | 224.2 | 229.8 | 235.7 | 237.2 | 0 |
| starter | 217.0 | 224.7 | 231.0 | 233.1 | 0 |
| streamliner | 209.2 | 220.5 | 225.6 | 229.4 | 0 |
| superbike | 219.5 | 232.8 | 231.1 | 239.5 | 0 |
| tourer | 232.0 | 237.5 | 239.1 | 245.0 | 0 |
| trike | 211.4 | 215.2 | 217.4 | 222.1 | 0 |
| trikester | 234.3 | 239.7 | 241.8 | 248.0 | 0 |

Raw results and worker logs are in `build/balance/{clear,rain,snow}/`. Reproduce with `BALANCE_WEATHER=<weather> tools/stock-karts/balance.sh` for all three weathers, then `python3 tools/stock-karts/weather_report.py`.

