# Stock vehicle weather balance

Two laps from a standing start, one AI-driven vehicle at a time, on Peach Pit, Foundry Flats, Launchpad Loop and Dune Drift. All 24 stock vehicles; clear, rain and snow; daytime. Clear uses the dry baseline seed 12345; rain and snow use seeds 12345, 54321, 8675309, reset before every race.

Each percentage is the mean of the vehicle's time divided by the median time on each course, minus one, averaged across seeds. Negative is quicker than the field; positive is slower. Each seed has its own field medians. The rain/snow change columns subtract the dry percentage: negative means the vehicle gains relative to its peers in that weather. These are percentage-point changes, not raw speed changes.

These are AI runs on four courses, not a measure of human performance or consistency on every course. Snow has no puddles; its extra seeds check race variation rather than puddle layouts. A DNF on any seed makes the weather's overall score DNF.

## Findings

- Clear: vehicles outside the usual roughly ±10% overall target: none.
- Rain: vehicles outside the usual roughly ±10% overall target: none.
- Snow: vehicles outside the usual roughly ±10% overall target: none.

The ±10% target applies to the four-course overall score; individual courses can show larger strengths and weaknesses. Changes to a vehicle apply in every weather, so any tuning also needs a dry recheck.

- Rain individual-seed outliers: none.
- Rain largest two-lap spread across seeds: 15.0 s (crusher on foundry_flats).
- Snow individual-seed outliers: none.
- Snow largest two-lap spread across seeds: 3.1 s (quarter_mile on foundry_flats).

## Relative pace

| Vehicle | Clear | Rain | Snow | Rain change | Snow change |
| --- | ---: | ---: | ---: | ---: | ---: |
| big_block | -6.7% | -9.0% | -9.4% | -2.4 pp | -2.7 pp |
| crusher | +9.3% | +3.5% | -2.3% | -5.9 pp | -11.6 pp |
| desert_pro | +0.4% | -3.7% | -6.4% | -4.2 pp | -6.8 pp |
| flat_track | -2.9% | -5.4% | -6.5% | -2.4 pp | -3.6 pp |
| flathead | +2.4% | +5.2% | +7.5% | +2.8 pp | +5.1 pp |
| gravel_rat | +4.1% | -1.3% | -3.6% | -5.4 pp | -7.7 pp |
| kart_kid | +1.9% | +5.0% | +5.7% | +3.1 pp | +3.8 pp |
| long_fork | -2.0% | -1.3% | +0.0% | +0.7 pp | +2.0 pp |
| long_haul | -2.2% | +0.4% | +2.3% | +2.6 pp | +4.5 pp |
| mudlark_quad | +5.1% | -1.2% | -5.0% | -6.3 pp | -10.0 pp |
| night_shift | -5.0% | -5.3% | -4.4% | -0.3 pp | +0.6 pp |
| oval_ace | -3.8% | -4.4% | -3.5% | -0.6 pp | +0.3 pp |
| quarter_mile | -3.6% | -0.5% | +4.6% | +3.0 pp | +8.2 pp |
| redline | -5.3% | -5.4% | -3.8% | -0.2 pp | +1.5 pp |
| sandhopper | +6.4% | +1.7% | -0.6% | -4.7 pp | -7.0 pp |
| scrambler | +7.4% | +4.5% | +2.7% | -2.9 pp | -4.6 pp |
| six_pack | +8.3% | +3.3% | -0.3% | -5.0 pp | -8.6 pp |
| streak | +0.7% | +4.3% | +6.0% | +3.6 pp | +5.3 pp |
| sunday_trike | -2.2% | +0.1% | +2.1% | +2.3 pp | +4.3 pp |
| tiddler | +2.6% | +3.3% | +4.5% | +0.7 pp | +1.8 pp |
| twin_nose | +4.8% | +8.1% | +9.9% | +3.3 pp | +5.1 pp |
| volt | -4.3% | -2.0% | +0.0% | +2.2 pp | +4.3 pp |
| zipper | -1.5% | -6.6% | -9.2% | -5.0 pp | -7.7 pp |
| zippy | -0.1% | +3.0% | +4.5% | +3.1 pp | +4.6 pp |

## Clear

96/96 runs finished; 0 resets in total.

Worker logs: 0 engine errors; 0 Jolt job-capacity warnings during concurrent runs.


### Seed 12345

Times are seconds for both laps.

| Vehicle | Peach Pit | Foundry Flats | Launchpad Loop | Dune Drift | Resets |
| --- | ---: | ---: | ---: | ---: | ---: |
| Field median | 162.3 | 169.9 | 175.0 | 177.1 | — |
| big_block | 159.0 | 157.3 | 161.7 | 159.9 | 0 |
| crusher | 183.8 | 184.9 | 190.1 | 188.8 | 0 |
| desert_pro | 162.4 | 170.8 | 177.5 | 176.4 | 0 |
| flat_track | 161.5 | 163.7 | 170.9 | 167.8 | 0 |
| flathead | 168.8 | 173.2 | 177.7 | 180.7 | 0 |
| gravel_rat | 168.8 | 177.5 | 183.2 | 182.5 | 0 |
| kart_kid | 166.6 | 174.1 | 176.6 | 179.5 | 0 |
| long_fork | 160.5 | 165.2 | 172.4 | 172.6 | 0 |
| long_haul | 161.8 | 165.1 | 170.4 | 171.5 | 0 |
| mudlark_quad | 176.2 | 177.1 | 184.7 | 180.4 | 0 |
| night_shift | 155.4 | 160.6 | 167.5 | 166.7 | 0 |
| oval_ace | 154.5 | 164.7 | 168.6 | 170.8 | 0 |
| quarter_mile | 155.7 | 160.2 | 171.6 | 172.4 | 0 |
| redline | 161.5 | 158.5 | 164.2 | 163.6 | 0 |
| sandhopper | 173.7 | 180.7 | 187.5 | 186.3 | 0 |
| scrambler | 176.6 | 184.5 | 185.4 | 187.9 | 0 |
| six_pack | 174.9 | 184.7 | 190.7 | 190.9 | 0 |
| streak | 162.3 | 171.9 | 175.3 | 179.5 | 0 |
| sunday_trike | 160.3 | 164.6 | 171.0 | 173.1 | 0 |
| tiddler | 169.7 | 173.3 | 179.1 | 180.1 | 0 |
| twin_nose | 174.1 | 178.7 | 180.1 | 183.5 | 0 |
| volt | 158.2 | 161.8 | 167.0 | 167.8 | 0 |
| zipper | 161.9 | 166.7 | 174.3 | 170.7 | 0 |
| zippy | 162.3 | 168.9 | 174.8 | 177.7 | 0 |

## Rain

288/288 runs finished; 13 resets in total.

Resets by course: foundry_flats: 13.

Worker logs: 0 engine errors; 7 Jolt job-capacity warnings during concurrent runs.

Overall relative pace by seed (same calculation as above, before averaging):

| Vehicle | 12345 | 54321 | 8675309 |
| --- | ---: | ---: | ---: |
| big_block | -9.0% | -9.1% | -9.1% |
| crusher | +4.8% | +2.7% | +2.8% |
| desert_pro | -3.7% | -3.8% | -3.8% |
| flat_track | -5.3% | -5.4% | -5.4% |
| flathead | +5.3% | +5.2% | +5.2% |
| gravel_rat | -1.3% | -1.3% | -1.3% |
| kart_kid | +5.0% | +5.0% | +4.9% |
| long_fork | -1.2% | -1.3% | -1.2% |
| long_haul | +0.4% | +0.4% | +0.3% |
| mudlark_quad | -1.2% | -1.2% | -1.2% |
| night_shift | -5.2% | -5.4% | -5.3% |
| oval_ace | -4.3% | -4.4% | -4.4% |
| quarter_mile | -0.4% | -0.6% | -0.6% |
| redline | -4.8% | -5.8% | -5.7% |
| sandhopper | +1.9% | +1.7% | +1.6% |
| scrambler | +4.6% | +4.5% | +4.4% |
| six_pack | +3.4% | +3.3% | +3.3% |
| streak | +4.5% | +4.3% | +4.1% |
| sunday_trike | +0.3% | +0.0% | +0.0% |
| tiddler | +3.4% | +3.5% | +3.0% |
| twin_nose | +8.1% | +8.0% | +8.1% |
| volt | -2.4% | -1.9% | -1.8% |
| zipper | -6.5% | -6.6% | -6.6% |
| zippy | +3.1% | +2.8% | +3.2% |

### Seed 12345

Times are seconds for both laps.

| Vehicle | Peach Pit | Foundry Flats | Launchpad Loop | Dune Drift | Resets |
| --- | ---: | ---: | ---: | ---: | ---: |
| Field median | 182.9 | 190.1 | 196.3 | 198.4 | — |
| big_block | 167.7 | 172.6 | 179.4 | 178.8 | 0 |
| crusher | 192.6 | 211.4 | 201.4 | 198.9 | 1 |
| desert_pro | 174.7 | 183.2 | 191.0 | 190.7 | 0 |
| flat_track | 171.8 | 179.1 | 189.2 | 187.0 | 0 |
| flathead | 195.0 | 201.1 | 203.9 | 208.1 | 0 |
| gravel_rat | 178.3 | 188.0 | 196.2 | 195.7 | 0 |
| kart_kid | 189.5 | 208.2 | 201.8 | 206.7 | 2 |
| long_fork | 177.8 | 187.2 | 195.7 | 198.0 | 0 |
| long_haul | 186.7 | 191.1 | 195.0 | 197.5 | 0 |
| mudlark_quad | 183.0 | 186.5 | 196.2 | 192.9 | 0 |
| night_shift | 169.3 | 180.7 | 188.8 | 189.3 | 0 |
| oval_ace | 169.2 | 183.3 | 190.1 | 192.3 | 0 |
| quarter_mile | 177.1 | 185.2 | 199.4 | 203.0 | 0 |
| redline | 172.9 | 186.4 | 185.0 | 186.7 | 2 |
| sandhopper | 184.8 | 195.7 | 201.4 | 200.5 | 0 |
| scrambler | 192.5 | 201.7 | 201.9 | 206.4 | 0 |
| six_pack | 185.7 | 199.4 | 204.6 | 204.0 | 0 |
| streak | 189.0 | 203.1 | 202.0 | 208.1 | 0 |
| sunday_trike | 182.8 | 190.4 | 196.3 | 200.2 | 0 |
| tiddler | 185.9 | 199.0 | 203.4 | 206.0 | 0 |
| twin_nose | 202.9 | 207.8 | 206.7 | 211.7 | 0 |
| volt | 174.6 | 189.7 | 191.3 | 193.6 | 0 |
| zipper | 170.2 | 176.6 | 186.7 | 184.2 | 0 |
| zippy | 185.8 | 199.1 | 201.1 | 205.5 | 0 |

### Seed 54321

Times are seconds for both laps.

| Vehicle | Peach Pit | Foundry Flats | Launchpad Loop | Dune Drift | Resets |
| --- | ---: | ---: | ---: | ---: | ---: |
| Field median | 182.9 | 190.8 | 196.2 | 198.4 | — |
| big_block | 167.6 | 172.6 | 179.2 | 179.1 | 0 |
| crusher | 192.6 | 196.4 | 201.1 | 198.8 | 0 |
| desert_pro | 174.7 | 183.1 | 190.9 | 190.8 | 0 |
| flat_track | 171.8 | 179.0 | 188.9 | 187.4 | 0 |
| flathead | 195.1 | 201.0 | 203.8 | 208.3 | 0 |
| gravel_rat | 178.3 | 188.1 | 196.1 | 195.8 | 0 |
| kart_kid | 189.6 | 208.4 | 201.8 | 206.7 | 2 |
| long_fork | 177.5 | 187.1 | 195.6 | 198.0 | 0 |
| long_haul | 186.7 | 192.0 | 194.8 | 197.7 | 0 |
| mudlark_quad | 183.0 | 186.6 | 196.2 | 192.9 | 0 |
| night_shift | 169.3 | 179.5 | 188.3 | 189.5 | 0 |
| oval_ace | 169.3 | 183.1 | 189.7 | 192.6 | 0 |
| quarter_mile | 177.1 | 185.1 | 199.3 | 202.9 | 0 |
| redline | 172.9 | 179.2 | 184.9 | 187.0 | 0 |
| sandhopper | 184.8 | 194.9 | 201.3 | 200.5 | 0 |
| scrambler | 192.5 | 201.6 | 201.9 | 206.4 | 0 |
| six_pack | 185.7 | 199.5 | 204.4 | 204.1 | 0 |
| streak | 188.9 | 202.3 | 201.4 | 208.4 | 0 |
| sunday_trike | 182.8 | 189.6 | 195.8 | 200.4 | 0 |
| tiddler | 185.9 | 200.2 | 203.0 | 206.3 | 0 |
| twin_nose | 202.6 | 208.1 | 206.8 | 211.8 | 0 |
| volt | 174.6 | 194.4 | 191.0 | 194.1 | 2 |
| zipper | 170.1 | 176.6 | 186.8 | 184.2 | 0 |
| zippy | 185.7 | 197.7 | 200.7 | 206.1 | 0 |

### Seed 8675309

Times are seconds for both laps.

| Vehicle | Peach Pit | Foundry Flats | Launchpad Loop | Dune Drift | Resets |
| --- | ---: | ---: | ---: | ---: | ---: |
| Field median | 183.0 | 190.9 | 196.2 | 198.3 | — |
| big_block | 167.8 | 172.8 | 179.2 | 178.7 | 0 |
| crusher | 192.7 | 196.6 | 201.3 | 198.8 | 0 |
| desert_pro | 174.7 | 183.2 | 190.9 | 190.6 | 0 |
| flat_track | 171.8 | 179.3 | 188.9 | 187.0 | 0 |
| flathead | 195.2 | 201.5 | 203.7 | 207.8 | 0 |
| gravel_rat | 178.4 | 188.1 | 196.2 | 195.6 | 0 |
| kart_kid | 189.6 | 208.6 | 201.8 | 206.3 | 2 |
| long_fork | 178.0 | 187.6 | 196.1 | 197.7 | 0 |
| long_haul | 186.8 | 191.8 | 194.8 | 197.1 | 0 |
| mudlark_quad | 183.1 | 186.8 | 196.2 | 192.8 | 0 |
| night_shift | 169.4 | 181.0 | 188.7 | 189.1 | 0 |
| oval_ace | 169.4 | 183.4 | 189.8 | 192.1 | 0 |
| quarter_mile | 177.2 | 185.6 | 198.8 | 202.6 | 0 |
| redline | 173.0 | 179.8 | 185.0 | 186.5 | 0 |
| sandhopper | 184.8 | 194.4 | 201.3 | 200.4 | 0 |
| scrambler | 192.5 | 201.7 | 201.9 | 206.3 | 0 |
| six_pack | 185.7 | 199.5 | 204.5 | 203.9 | 0 |
| streak | 189.7 | 200.9 | 201.5 | 207.6 | 0 |
| sunday_trike | 182.9 | 190.0 | 195.9 | 199.8 | 0 |
| tiddler | 186.1 | 197.0 | 203.0 | 205.6 | 0 |
| twin_nose | 203.3 | 208.4 | 207.1 | 211.5 | 0 |
| volt | 174.8 | 194.9 | 191.2 | 193.5 | 2 |
| zipper | 170.2 | 176.7 | 186.9 | 184.1 | 0 |
| zippy | 186.1 | 200.7 | 200.8 | 205.1 | 0 |

## Snow

288/288 runs finished; 16 resets in total.

Resets by course: foundry_flats: 16.

Worker logs: 0 engine errors; 3 Jolt job-capacity warnings during concurrent runs.

Overall relative pace by seed (same calculation as above, before averaging):

| Vehicle | 12345 | 54321 | 8675309 |
| --- | ---: | ---: | ---: |
| big_block | -9.4% | -9.4% | -9.4% |
| crusher | -2.2% | -2.3% | -2.3% |
| desert_pro | -6.4% | -6.4% | -6.4% |
| flat_track | -6.5% | -6.5% | -6.5% |
| flathead | +7.5% | +7.5% | +7.5% |
| gravel_rat | -3.6% | -3.7% | -3.7% |
| kart_kid | +5.7% | +5.7% | +5.7% |
| long_fork | +0.1% | +0.0% | +0.0% |
| long_haul | +2.3% | +2.3% | +2.3% |
| mudlark_quad | -4.9% | -5.0% | -5.0% |
| night_shift | -4.4% | -4.4% | -4.4% |
| oval_ace | -3.5% | -3.5% | -3.5% |
| quarter_mile | +4.8% | +4.4% | +4.4% |
| redline | -3.8% | -3.8% | -3.8% |
| sandhopper | -0.6% | -0.6% | -0.6% |
| scrambler | +2.8% | +2.7% | +2.7% |
| six_pack | -0.3% | -0.3% | -0.3% |
| streak | +6.0% | +5.9% | +5.9% |
| sunday_trike | +2.2% | +2.1% | +2.1% |
| tiddler | +4.5% | +4.5% | +4.5% |
| twin_nose | +9.9% | +9.8% | +9.8% |
| volt | +0.0% | +0.0% | +0.0% |
| zipper | -9.2% | -9.2% | -9.2% |
| zippy | +4.5% | +4.5% | +4.5% |

### Seed 12345

Times are seconds for both laps.

| Vehicle | Peach Pit | Foundry Flats | Launchpad Loop | Dune Drift | Resets |
| --- | ---: | ---: | ---: | ---: | ---: |
| Field median | 200.8 | 216.7 | 220.0 | 222.3 | — |
| big_block | 181.6 | 194.6 | 200.8 | 202.0 | 0 |
| crusher | 202.5 | 210.1 | 214.5 | 212.9 | 0 |
| desert_pro | 189.4 | 200.1 | 206.7 | 208.5 | 0 |
| flat_track | 186.7 | 198.3 | 210.0 | 209.3 | 0 |
| flathead | 222.8 | 230.2 | 232.5 | 238.0 | 0 |
| gravel_rat | 192.4 | 211.3 | 211.9 | 213.1 | 2 |
| kart_kid | 215.1 | 229.1 | 229.0 | 235.3 | 0 |
| long_fork | 201.5 | 213.1 | 221.1 | 224.7 | 0 |
| long_haul | 212.7 | 219.6 | 221.3 | 225.4 | 0 |
| mudlark_quad | 193.7 | 200.6 | 212.2 | 210.6 | 0 |
| night_shift | 188.9 | 205.5 | 213.0 | 215.0 | 0 |
| oval_ace | 189.6 | 210.6 | 213.1 | 217.1 | 0 |
| quarter_mile | 207.9 | 227.3 | 231.7 | 234.5 | 2 |
| redline | 193.6 | 208.3 | 211.1 | 214.4 | 0 |
| sandhopper | 198.5 | 222.3 | 216.4 | 217.6 | 1 |
| scrambler | 209.5 | 221.8 | 223.4 | 228.4 | 0 |
| six_pack | 198.7 | 215.7 | 221.4 | 221.3 | 0 |
| streak | 216.5 | 228.7 | 228.8 | 236.8 | 0 |
| sunday_trike | 207.8 | 220.4 | 222.2 | 227.7 | 1 |
| tiddler | 210.5 | 224.3 | 229.5 | 233.9 | 0 |
| twin_nose | 232.1 | 236.2 | 234.2 | 241.0 | 0 |
| volt | 200.0 | 217.7 | 219.0 | 223.3 | 0 |
| zipper | 183.4 | 191.0 | 203.5 | 202.6 | 0 |
| zippy | 212.2 | 224.5 | 227.8 | 233.8 | 0 |

### Seed 54321

Times are seconds for both laps.

| Vehicle | Peach Pit | Foundry Flats | Launchpad Loop | Dune Drift | Resets |
| --- | ---: | ---: | ---: | ---: | ---: |
| Field median | 200.8 | 216.8 | 220.0 | 222.3 | — |
| big_block | 181.6 | 194.6 | 200.8 | 202.0 | 0 |
| crusher | 202.5 | 210.0 | 214.5 | 212.9 | 0 |
| desert_pro | 189.4 | 200.1 | 206.7 | 208.5 | 0 |
| flat_track | 186.7 | 198.3 | 210.0 | 209.3 | 0 |
| flathead | 222.8 | 230.2 | 232.5 | 238.0 | 0 |
| gravel_rat | 192.4 | 211.3 | 211.9 | 213.1 | 2 |
| kart_kid | 215.1 | 229.1 | 229.0 | 235.3 | 0 |
| long_fork | 201.5 | 213.1 | 221.1 | 224.7 | 0 |
| long_haul | 212.7 | 219.6 | 221.3 | 225.4 | 0 |
| mudlark_quad | 193.7 | 200.6 | 212.2 | 210.6 | 0 |
| night_shift | 188.9 | 205.5 | 212.8 | 215.0 | 0 |
| oval_ace | 189.6 | 210.7 | 213.1 | 217.1 | 0 |
| quarter_mile | 207.9 | 224.2 | 231.8 | 234.5 | 1 |
| redline | 193.6 | 208.2 | 211.1 | 214.4 | 0 |
| sandhopper | 198.5 | 222.5 | 216.4 | 217.6 | 1 |
| scrambler | 209.5 | 221.8 | 223.4 | 228.4 | 0 |
| six_pack | 198.7 | 216.0 | 221.4 | 221.3 | 0 |
| streak | 216.5 | 228.7 | 228.8 | 236.8 | 0 |
| sunday_trike | 207.8 | 220.4 | 222.2 | 227.7 | 1 |
| tiddler | 210.5 | 224.3 | 229.5 | 233.9 | 0 |
| twin_nose | 232.1 | 236.2 | 234.2 | 241.0 | 0 |
| volt | 200.0 | 217.7 | 219.0 | 223.3 | 0 |
| zipper | 183.4 | 191.0 | 203.5 | 202.6 | 0 |
| zippy | 212.2 | 224.5 | 227.8 | 233.8 | 0 |

### Seed 8675309

Times are seconds for both laps.

| Vehicle | Peach Pit | Foundry Flats | Launchpad Loop | Dune Drift | Resets |
| --- | ---: | ---: | ---: | ---: | ---: |
| Field median | 200.8 | 216.8 | 220.0 | 222.3 | — |
| big_block | 181.6 | 194.6 | 200.8 | 202.0 | 0 |
| crusher | 202.5 | 210.0 | 214.5 | 212.9 | 0 |
| desert_pro | 189.4 | 200.1 | 206.7 | 208.5 | 0 |
| flat_track | 186.7 | 198.3 | 210.0 | 209.3 | 0 |
| flathead | 222.8 | 230.2 | 232.5 | 238.0 | 0 |
| gravel_rat | 192.4 | 211.3 | 211.9 | 213.1 | 2 |
| kart_kid | 215.1 | 229.1 | 229.0 | 235.3 | 0 |
| long_fork | 201.5 | 213.1 | 221.1 | 224.7 | 0 |
| long_haul | 212.7 | 219.6 | 221.3 | 225.4 | 0 |
| mudlark_quad | 193.7 | 200.6 | 212.2 | 210.6 | 0 |
| night_shift | 188.9 | 205.5 | 212.8 | 215.0 | 0 |
| oval_ace | 189.6 | 210.7 | 213.1 | 217.1 | 0 |
| quarter_mile | 207.9 | 224.2 | 231.8 | 234.5 | 1 |
| redline | 193.6 | 208.2 | 211.1 | 214.4 | 0 |
| sandhopper | 198.5 | 222.5 | 216.4 | 217.6 | 1 |
| scrambler | 209.5 | 221.8 | 223.4 | 228.4 | 0 |
| six_pack | 198.7 | 216.0 | 221.4 | 221.3 | 0 |
| streak | 216.5 | 228.7 | 228.8 | 236.8 | 0 |
| sunday_trike | 207.8 | 220.4 | 222.2 | 227.7 | 1 |
| tiddler | 210.5 | 224.3 | 229.5 | 233.9 | 0 |
| twin_nose | 232.1 | 236.2 | 234.2 | 241.0 | 0 |
| volt | 200.0 | 217.7 | 219.0 | 223.3 | 0 |
| zipper | 183.4 | 191.0 | 203.5 | 202.6 | 0 |
| zippy | 212.2 | 224.5 | 227.8 | 233.8 | 0 |

Raw results and worker logs are in `build/balance/<weather>/` for seed 12345 and `build/balance/<weather>/seed_<seed>/` for other seeds. Reproduce with:

```sh
tools/stock-karts/balance.sh
for weather in rain snow; do
  for seed in 12345 54321 8675309; do
    BALANCE_WEATHER="$weather" BALANCE_SEED="$seed" tools/stock-karts/balance.sh
  done
done
python3 tools/stock-karts/weather_report.py --seeds 12345 54321 8675309 > tools/stock-karts/weather_balance.md
```
