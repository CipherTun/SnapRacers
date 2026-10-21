# SnapRacers

SnapRacers is a physics based kart racing game I put together for my son. Build a kart from blocks and race it, then change the parts until it drives how you want. Every part adds weight, drag or power. Crashes knock parts off, and the reset button puts them back with a short slowdown.

You can race the AI, play with a friend on a split screen or race online. There are nine Grand Prix cups and 36 courses, and you can make your own courses and cups too. It needs Android 8.1 or newer, or you can play it in a browser.

It's playable now, but there are still rough edges. Let me know if you find one.

Cheers,<br>
Dan

---

## Screenshots

<table>
  <tr>
    <td align="center"><img src="screenshots/race.png" width="400" height="225" alt="Racing at Coral Cove in the Island Cup"></td>
    <td align="center"><img src="screenshots/garage.png" width="400" height="225" alt="The garage"></td>
  </tr>
  <tr>
    <td align="center"><img src="screenshots/rain-night.png" width="400" height="225" alt="Rain and course lighting at night at Peach Pit"></td>
    <td align="center"><img src="screenshots/snow.png" width="400" height="225" alt="Snow racing at Frostbite Forest"></td>
  </tr>
  <tr>
    <td align="center"><img src="screenshots/cups.png" width="400" height="225" alt="All nine Grand Prix cups"></td>
    <td align="center"><img src="screenshots/karts.png" width="400" height="225" alt="The kart picker"></td>
  </tr>
  <tr>
    <td align="center"><img src="screenshots/driver.png" width="400" height="225" alt="The driver screen"></td>
    <td align="center"><img src="screenshots/editor.png" width="400" height="225" alt="The track editor"></td>
  </tr>
</table>

---

## Installing

Add [my F-Droid repo](https://hunke.ws/fdroid/repo?fingerprint=80438B253C257BCCE05CDCB9E3AC9B6174C2250659962B14FCBE7F32FD42D53E), then search for SnapRacers. F-Droid will offer new versions as updates and pick the right build for your phone.

You can also get an APK from [Releases](https://github.com/roge-rm/SnapRacers/releases). Use the usual APK, or the one marked `32bit` for older phones and tablets that need it. Both need Android 8.1 or newer.

## Playing in a browser

[Play SnapRacers](https://hunke.ws/fdroid/play/snapracers/) in a browser with WebGL 2. Your karts, drivers, courses and records are saved in that browser. Two players can share a keyboard or use controllers. To race online from the browser, join a dedicated server.

## Racing

Grand Prix has nine cups of four races, with points and trophies. From the second race on, the leader starts at the back. Finish in the top three for a gold, silver or bronze trophy, kept separately for each difficulty. You can also make cups of 2 to 8 races from any courses.

Single race is one race against the AI, time trial keeps your best times and practice lets you drive on your own for as long as you like. There are four AI levels, from Easy drivers who wait for you and make mistakes to Expert drivers who drive on the limit and slide through bends.

Two players can race one course or a whole Grand Prix from the Multiplayer menu. On a phone you can play side by side in landscape, or face to face in portrait with the phone flat between you. Each player picks a kart and enters their name.

There are seven camera views: close chase, far chase, first person, hood, bumper, overhead and TV cameras beside the track. Hold look back to see behind you. After the finish the camera circles your kart and the AI drives it home.

To slide, hold the gas and brake together while steering. On a touch screen you can slide your thumb from GO down onto the brake and back up. Keep the gas on and steer into the bend to hold the slide, then straighten up to grip again. Hold it for at least half a second and straighten up with the gas still on for a little turbo. A longer slide gives more turbo but loses more speed.

Grass and sand slow you down, and a slide ends as soon as a wheel leaves the road. Sand slows you more than grass. If you get stuck or lose parts, reset puts you upright and repairs the kart. You slow down briefly and go through other karts for one second.

The button in the corner, or Start on a controller, opens the race menu. It pauses a race on your own or in split screen, where either player can carry on. Online the race keeps going while your menu is open.

### Power-ups

Drive through a gold stud to get a power-up. You can hold two at once, one on each gadget button. Karts further back have a better chance of getting a strong one.

| Power-up | What it does |
|---|---|
| Turbos | A short boost, a longer boost or three boosts to use separately. |
| Tow rope | Pulls you behind the kart ahead for three seconds, then lets go with a burst. |
| Bricks and traps | Drop bricks, a wall, marbles or spikes behind you. Spikes slow karts and knock parts off. |
| Shockwave | Shoves nearby karts away and knocks parts off the closest ones. |
| Cannonball | Fires ahead, knocks three parts off the kart it hits and shoves it. A shield keeps the parts on but still lets it be shoved. |
| Homing brick | Follows the road to the kart ahead and knocks one part off. |
| Shield | Protects your parts for four seconds. |
| Repair kit | Puts back your lost parts without the reset slowdown. |
| Ghost | Lets you pass through karts, bricks and traps for three seconds. |
| Lightning | Strikes every kart ahead and slows them for five seconds. |

## The garage

Drag a part from the drawer onto the kart. It snaps on where its studs, clips, pins or axles fit, and dots show the places it can go. Tap a part to move, turn, flip, slide, copy or delete it. Mirror builds on both sides at once, and you can paint each part in sixteen brick colours.

Undo and redo changes, save as many karts as you like or start from a stock kart. The card in the corner shows speed, pull, cornering, control, off-road grip, weight and drag. The wind button shows where the drag comes from, and you can take the kart straight out for a test drive.

### Parts

There are 289 parts. I modelled most of them in `tools/parts`.

| Parts | What's there |
|---|---|
| Plates | Small plates, long and wide chassis plates, tiles, grilles and wedges. |
| Bricks | Plain and round bricks, brackets, race numbers, headlights and ballast. |
| Curves | Slopes, nose cones, arches, fairings, side pods and a ram plate. |
| Car bodies | Bonnets, cabs, engine covers, scoops, dragster bodies, roll cages, mudguards, exhausts and wheelie bars. |
| Rods and joints | Bars, clips, beams, pins, axles, hinges and ball joints. |
| Wheels | Kart, truck, dragster, quad, scooter and motorbike wheels, from tiny to monster truck size. |
| Engines | Petrol and electric engines, a diesel, V8s, a jet and pedals. Each sounds different. |
| Cockpit | Seats, steering wheels, handlebars, windscreens, canopies, mirrors and lights. |
| Bikes, trikes and quads | Frames, forks, bodywork, saddles, tanks, footpegs and fairings. |
| Wings | Front and rear wings, spoilers and a ducktail. |

Slick tires grip the road best, knobbly tires handle dirt and grass, studded tires help on ice and balloon tires handle sand and curbs. Skinny wheels roll further.

The kart's shape decides its drag. Flat faces catch the wind, slopes and nose cones let it past, and fairings help around open wheels. A windscreen shelters the driver. Lying down keeps the driver out of the wind too, but slows their steering. Put the steering close to the seat, the further they reach the slower their hands move.

### Stock vehicles

You can pick any of the 24 stock vehicles before a race. The AI uses them too, picking one at random for a race or a whole Grand Prix. Their lap times are within about ten percent of each other overall.

| Vehicle | How it drives |
|---|---|
| Kart Kid | A light little go-kart with the engine beside the seat. Easy to learn on. |
| Redline | A formula racer with open wheels and wings. Quick through fast corners. |
| Big Block | A heavy muscle car with a big engine. Slow to get going, then quick. |
| Oval Ace | A stock car with a roof and a rear spoiler. Steady and easy to drive. |
| Gravel Rat | A rally car with knobbly tires and four lamps. Good on dirt and gravel. |
| Night Shift | An endurance racer with the driver lying under a canopy. Fast and smooth. |
| Quarter Mile | A dragster with a blower V8 and huge slicks. Fast on straights, slow in corners. |
| Flathead | A hot rod with a blower V8. Plenty of pull and a handful to drive. |
| Sandhopper | A dune buggy with a roll cage. Good on sand and grass. |
| Volt | An electric racer with wings. Quick off the line and easy to drive. |
| Crusher | A tall monster truck. Rolls over bumps but needs care in corners. |
| Long Haul | A big rig without a trailer. Slow to start and stop, and shoves other karts about. |
| Desert Pro | A desert racer on big knobbly tires. Good on rough ground and the road. |
| Six Pack | A truck with two rear axles. Plenty of grip but slow to turn. |
| Streak | A low superbike with fairings. Fast, but gets knocked about and takes bends wider than a kart. |
| Scrambler | A dirt bike. Good on grass and bumps, slower to turn on tarmac. |
| Zippy | A little scooter. Quick off the line, with a low top speed. |
| Long Fork | A chopper with a long fork. Fast on straights but slow to turn. |
| Twin Nose | A trike with two front wheels. Leans into bends and corners nearly like a kart. |
| Sunday Trike | A chopper trike with a rounded rear body. Steady but slow to turn. |
| Tiddler | A little electric trike with a rear box. Slow, steady and easy to drive. |
| Zipper | A sport quad. Corners flat and handles grass well. |
| Mudlark | A tall quad on big knobbly wheels. Good off the road, slow on tarmac. |
| Flat Track | A low racing quad on wide wheels. Sharp in bends, with little grip on grass. |

## Drivers

Build a driver from a face, hair, facial hair, headgear, neckwear, a torso, a back piece, arms and legs. There are at least twenty choices for each, and you can change their colours. Heavier clothes and accessories make a heavier driver and a steadier kart. The seven AI drivers use the same parts.

The figures blink, watch nearby karts, grin when they pass someone and look cross when they're passed. The winner throws their fists in the air. On the driver screen they look around, wave and hop when you try a new part.

## Courses

The 36 courses are based on real circuits, with laps of 1.6 to 1.9 km. They're built from track pieces on a grid, with hills, jumps, bridges, a loop and corkscrews. The road is wide enough for three karts through a bend.

| Cup | Courses |
|---|---|
| Baseplate | Peach Pit, Trulli Turns, Lemon Lake, Pithead Park |
| Axle | Delta Dash, Bucketwheel Bend, Foundry Flats, Amber Arc |
| Gearbox | Timberline, Frostbite Forest, Dune Drift, Whistlestop Woods |
| Keystone | Windmill Ridge, Launchpad Loop, Magma Mile, Castle Keep |
| Legends | Royal Run, Dry Lagoon, Sakura Swirl, Rouge Ridge |
| Gravel | Menhir Meadow, Oast Hill, Devil's Dust, Pine Hill Leap |
| Hangar | Neon Nights, Hairpin Hall, Bohemian Bends, Spark Deck |
| Corkscrew | Serpent Summit, Lakeshore Plunge, Red Rocket, Twister Pines |
| Island | Windsurf Way, Coral Cove, Blue Lagoon, Penguin Point |

The Legends Cup shrinks famous race tracks to kart size. Gravel mixes tarmac and gravel on rallycross circuits. Hangar has indoor tracks, one with an upper deck. Corkscrew follows roller coasters with drops and upside-down bends, and Island races beside the sea.

Walls keep you from falling off, and tire stacks stop you cutting between nearby bits of road. Curbs can bounce your wheels into the air. Trees, fences and billboards break apart when you hit them, and crashes knock holes in buildings and grandstands. The loose bricks stay until the race ends. Tire stacks lose their top tires but keep the bottom ones.

Crowds cheer and wave as you pass. Windmills turn, flags wave, cranes swing and boats rock on the water.

### Track editor

Tap pieces onto the end of the road like a slot car set. There are straights, bends, S bends, humps, ramps, jumps, loops, wall rides, banked bends and shortcuts. Tap a piece to remove it, add pieces after it, change its surface or add and remove walls.

Close it up joins the road back to the start with as few pieces as it can. The card in the corner says what's stopping the course being raced. Pick the ground, colours, trees and hills, then place landmarks like windmills, castles and lighthouses.

Saving puts the start line on the longest straight. Your course then appears in the race lists with its own records.

### Sharing courses and cups

Share a course or cup as a code or a file. A course code is about 400 characters, so you can paste it into a message. On a phone you can send either through the share sheet. On a computer you copy the code or save the file, and in a browser you download it.

Use Add a course or Add a cup to paste a code or open a file. Cups include their courses, and copies aren't added twice. Online the host sends the course or cup to everyone. Keep in the lobby saves it to yours.

## Weather and time of day

Pick the weather and time beside the difficulty, or leave them to chance. A course can have its own set in the editor.

- Morning, day, evening, dusk and night change the sun, sky and shadows. At night the moon casts fainter shadows.
- Rain makes the road shiny and slippery. Puddles slow you and grip less again.
- Snow covers the ground and scenery. The cleared road is wet and slippery.
- Fog hides the distance, storms bring heavy rain and lightning, and dust storms cover sandy courses.
- Course lamps and kart lights come on when it's dark. Headlights light the road and tail lights brighten when you brake.

Left to chance, the weather suits the course. Snowy courses mostly get snow, deserts get dust storms and no rain, and beaches are mostly sunny. Indoor courses stay the same. Time trials default to a clear day.

Outdoor records count only in clear daytime, and indoor runs always count. Other conditions still show your times. The AI adjusts its driving, and everyone online gets the same weather and puddles.

## Controls

Touch, controllers and keys work in the menus, races, garage, driver screen and track editor. Each player picks a controller and changes their keys and buttons in Settings. Tap a binding, then press its replacement.

Power-ups start on LB and RB. Pick the Xbox or Switch button layout in Settings. A Switch controller uses the names printed on its buttons. Press A on a name box to open the screen keyboard, X to delete, Y for a space and Start to finish.

## Online

Up to eight karts can race together, with AI in the empty places if the host wants them. The host picks a race or cup. Two players sharing one phone can join together.

- On the same Wi-Fi, host on one phone and its game appears on the others.
- For a hotspot, turn it on, join it with the other phones and host on that phone.
- For Wi-Fi Direct, host over Wi-Fi Direct and use Find Wi-Fi Direct games on the others.
- For Bluetooth, pair two or three phones, then host and join over Bluetooth.
- A dedicated server runs races on your network or the internet, with an admin page. Phones and browsers can join it. See [server/README.md](server/README.md).

How do I connect? at the bottom of the online screen has the steps.

## Graphics and sound

Change the graphics in Settings under Display. Medium and Low draw at a lower resolution while keeping the menus sharp. They reduce shadows, distant scenery, crowds, rain and snow. Low draws headlight beams only for your kart, Medium for nearby karts and High for karts up to 40 metres away. Things you can drive into stay in place at every setting.

I made the sounds and music with a little synthesizer in `tools/sound`. Each engine has its own sound. Tires squeal, surfaces rumble, bricks clatter and the wind gets louder as you speed up. There's a menu tune and one for each cup. Music and effects have separate volume controls in Settings.

## Building

SnapRacers uses Godot 4.7.2, the Compatibility renderer and Jolt physics. The scripts expect these local tools, which aren't in the repo:

- `tools/godot/Godot_v4.7.2-stable_linux.x86_64`, with an empty `._sc_` file beside it to keep settings in `tools/godot/editor_data`
- Godot 4.7.2 export templates in `tools/godot/editor_data/export_templates/4.7.2.stable`
- Android SDK and Java 21, set under Export › Android in the editor settings

```sh
tools/build-engine.sh             # Android engines, arm64 and x86_64
tools/build-engine.sh --release   # with full optimisation for a release
tools/build-engine.sh arm32       # engine for older 32-bit phones
tools/build-android.sh            # phone APK, arm64
tools/build-android.sh --arm32    # phone APK, 32-bit
tools/build-android.sh --install  # x86_64 APK, installed on SnapRacers_Pixel_5
tools/build-engine.sh web         # browser engine
tools/build-web.sh                # browser build in build/web
tools/build-web.sh --serve        # serve over HTTPS on port 8060
tools/build-plugin.sh             # Android network plugin
tools/build-server.sh --run       # build and run a local dedicated server
```

The custom engine includes only what the game uses, listed in `tools/engine/profile.py`. Building it needs the Android NDK and `uv` for scons. Build it once, then again when Godot or the profile changes. The Android build uses the stock engine if the custom one isn't there.

The browser engine needs [Emscripten](https://emscripten.org) in `~/.local/share/emsdk` or at `EMSDK`. It runs without threads and can be served as static files.

The Android network plugin is Kotlin code in `android-plugin` for NSD, Wi-Fi Direct and Bluetooth. The Android build rebuilds it when needed, using Gradle from Godot's Android template. `addons/snapracers_net` adds it to the APK.

Phone builds use my release key from `../Keys` when it's available, otherwise the Android debug key. Build output and the engine compile cache go in `build/`.

The game code is in `scripts`, and parts, karts, drivers and courses are JSON in `data`. [tools/parts](tools/parts/README.md), [tools/characters](tools/characters/README.md) and [tools/sound](tools/sound/README.md) make the models and sounds. [tools/stock-karts](tools/stock-karts/README.md) builds and compares stock vehicles, and [tools/track-design](tools/track-design/README.md) turns real circuits into track pieces.

## Testing

Run the headless tests on the computer:

```sh
tools/run-tests.sh
```

They check driving, building, damage, power-ups, weather, cameras, menus, controllers, sharing, courses and race modes. They also drive every stock vehicle around a lap and race two copies of the game over the network. Network and dedicated-server races run in real time, so the suite takes a while.

To check AI steering and overtaking, or race eight AI karts around all 36 courses:

```sh
tools/godot/Godot_v4.7.2-stable_linux.x86_64 --headless --fixed-fps 60 --path . -s tests/ai_drive_test.gd
tools/soak/soak.sh
```

The soak writes logs for each course and `summary.txt` in `build/soak`. You can give it course names to run only those courses, for example `tools/soak/soak.sh peach_pit launchpad_loop`.

The dedicated-server test works on its own server or a running one with `tools/run-server-test.sh --running`. See [server/README.md](server/README.md) for Docker and server setup.

## Licence

SnapRacers is free software under the GNU General Public License, version 3 or later. See [LICENSE](LICENSE).

Copyright © 2026 Dan Hunke.

It uses the [Godot Engine](https://godotengine.org), under the MIT licence. Courses are traced from OpenStreetMap map data, © OpenStreetMap contributors, under the Open Database Licence.

Disclaimer: I am not a great programmer and this was made using Claude Opus 5.5
