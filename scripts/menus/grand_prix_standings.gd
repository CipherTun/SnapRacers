class_name GrandPrixStandings
extends Control

## The points table between Grand Prix races, and the trophy at the end.
##
## Online, the host moves everyone on to the next race (and back to the lobby
## at the end), and a cup raced online doesn't count toward your trophies.
## For two on this phone both players show in their colours, and the trophy
## goes by whichever of them did better.

var grand_prix: GrandPrix


func _init(gp: GrandPrix) -> void:
	grand_prix = gp


func _ready() -> void:
	var done := grand_prix.finished()
	var races := grand_prix.track_ids().size()
	var level := Difficulty.name_of(grand_prix.difficulty)
	var title: String = "%s, %s" % [grand_prix.cup.name, level] if done else "%s, %s, after race %d of %d" % [grand_prix.cup.name, level, grand_prix.round, races]
	var column := MenuStyle.page(self, title, go_back, 620.0)
	var standings := grand_prix.standings()
	var people: Array = grand_prix.people if not grand_prix.people.is_empty() else [Game.player_name()]
	var names := standings.map(func(s): return s[0])
	var place := grand_prix.best_place() if not grand_prix.people.is_empty() else names.find(people[0]) + 1
	if done:
		var trophy: String = CupGrid.TROPHIES.get(place, "")
		var news := "You won the %s!" % grand_prix.cup.name if place == 1 else "You finished %s." % RaceHud.ordinal(place)
		if grand_prix.two and place > 0:
			var who: String = names[place - 1]
			news = "%s won the %s!" % [who, grand_prix.cup.name] if place == 1 else "%s finished %s." % [who, RaceHud.ordinal(place)]
		if trophy != "":
			news += " That's a %s." % trophy.to_lower()
		var banner := Label.new()
		banner.text = news
		banner.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		banner.add_theme_font_size_override("font_size", 30)
		banner.add_theme_color_override("font_color", MenuStyle.ACCENT)
		column.add_child(banner)
		if not Game.net.is_online():
			Records.add_cup_place(grand_prix.cup.id, place, grand_prix.difficulty, grand_prix.two)
	var table := GridContainer.new()
	table.columns = 3
	table.add_theme_constant_override("h_separation", 40)
	table.add_theme_constant_override("v_separation", 6)
	column.add_child(table)
	for i in standings.size():
		for text in [RaceHud.ordinal(i + 1), standings[i][0], "%d points" % standings[i][1]]:
			var cell := Label.new()
			cell.text = text
			cell.add_theme_font_size_override("font_size", 24)
			var person := people.find(standings[i][0])
			if person >= 0:
				var colour: Color = KartPicker.PLAYER_COLOURS[mini(person, KartPicker.PLAYER_COLOURS.size() - 1)] if grand_prix.two else Color("#f2cd37")
				cell.add_theme_color_override("font_color", colour)
			table.add_child(cell)
	if Game.net.is_online():
		if Game.net.is_host():
			var carry_on := MenuStyle.button("Back to the lobby" if done else "Next race", Game.net.back_to_lobby if done else Game.net.next_round)
			carry_on.custom_minimum_size.y = 84.0
			column.add_child(carry_on)
		else:
			column.add_child(MenuStyle.heading("Waiting for the host to carry on"))
	elif done:
		var two := grand_prix.two
		column.add_child(MenuStyle.button("Race another cup", func() -> void:
			Game.grand_prix = null
			Game.show_cups(two)))
	else:
		var next := TrackPath.load_file(grand_prix.track_path())
		var button := MenuStyle.button("Next race", Game.next_grand_prix_race, next.name)
		button.custom_minimum_size.y = 84.0
		column.add_child(button)


## Leaving here quits the cup (and, online, the game).
func go_back() -> void:
	var two := grand_prix.two
	Game.grand_prix = null
	if Game.net.is_online():
		Game.net.leave()
		Game.show_multiplayer()
		return
	Game.show_cups(two)
