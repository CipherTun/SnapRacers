class_name EditorsMenu
extends Control

## Where you make things of your own, like a kart in the garage, a driver to
## sit in it and courses to race on. Back from any of them comes here.


func _ready() -> void:
	var column := MenuStyle.menu_screen(self, "Editors")
	for item in [
		["Garage", Game.show_garage, "Build your kart out of bricks and parts", "wrench"],
		["Driver", Game.show_driver, "Choose who's driving, and how they look", "person"],
		["Track editor", Game.show_track_editor, "Lay out a course of your own and race on it", "track"],
	]:
		column.add_child(MenuStyle.big_button(item[0], item[3], item[1], item[2]))
	MenuStyle.back_at_bottom(column, Game.show_menu)


func go_back() -> void:
	Game.show_menu()
