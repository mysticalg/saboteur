extends Node2D

const GRAVITY := 1800.0
const RUN_SPEED := 280.0
const JUMP_SPEED := -650.0
const PLAYER_SIZE := Vector2(30, 52)

var player_pos := Vector2(80, 560)
var player_vel := Vector2.ZERO
var on_ground := false

var has_bomb := false
var has_codes := false
var bomb_armed := false
var bomb_defused := false
var can_extract := false
var mission_time := 120.0
var game_over := false
var win := false

var solids: Array[Rect2] = [
	Rect2(0, 680, 2200, 80),
	Rect2(240, 600, 200, 20),
	Rect2(560, 530, 180, 20),
	Rect2(840, 460, 200, 20),
	Rect2(1160, 390, 220, 20),
	Rect2(1500, 320, 220, 20),
]

var bomb_rect := Rect2(280, 560, 20, 20)
var codes_rect := Rect2(890, 420, 20, 20)
var terminal_rect := Rect2(1520, 280, 26, 36)
var extraction_rect := Rect2(2040, 640, 40, 40)

func _ready() -> void:
	set_physics_process(true)
	queue_redraw()

func _physics_process(delta: float) -> void:
	if game_over:
		if Input.is_action_just_pressed("ui_accept"):
			reset_game()
		return

	var dir := Input.get_axis("ui_left", "ui_right")
	player_vel.x = dir * RUN_SPEED

	if Input.is_action_just_pressed("ui_accept") and on_ground:
		player_vel.y = JUMP_SPEED

	player_vel.y += GRAVITY * delta

	# Horizontal sweep
	player_pos.x += player_vel.x * delta
	var p := player_rect()
	for wall in solids:
		if p.intersects(wall):
			if player_vel.x > 0:
				player_pos.x = wall.position.x - PLAYER_SIZE.x
			elif player_vel.x < 0:
				player_pos.x = wall.end.x
			player_vel.x = 0
			p = player_rect()

	# Vertical sweep
	on_ground = false
	player_pos.y += player_vel.y * delta
	p = player_rect()
	for wall in solids:
		if p.intersects(wall):
			if player_vel.y > 0:
				player_pos.y = wall.position.y - PLAYER_SIZE.y
				on_ground = true
			elif player_vel.y < 0:
				player_pos.y = wall.end.y
			player_vel.y = 0
			p = player_rect()

	var interact := Input.is_action_just_pressed("ui_select")
	var pickup_zone := player_rect().grow(8)

	if not has_bomb and pickup_zone.intersects(bomb_rect):
		has_bomb = true
		bomb_armed = true

	if not has_codes and pickup_zone.intersects(codes_rect):
		has_codes = true

	if interact and pickup_zone.intersects(terminal_rect) and bomb_armed and has_codes:
		bomb_defused = true

	can_extract = has_bomb and has_codes and bomb_defused
	if can_extract and pickup_zone.intersects(extraction_rect):
		win = true
		game_over = true

	if bomb_armed and not bomb_defused:
		mission_time = max(0.0, mission_time - delta)
		if mission_time <= 0.0:
			win = false
			game_over = true

	queue_redraw()

func player_rect() -> Rect2:
	return Rect2(player_pos, PLAYER_SIZE)

func _draw() -> void:
	# World
	for wall in solids:
		draw_rect(wall, Color(0.2, 0.22, 0.27), true)

	if not has_bomb:
		draw_rect(bomb_rect, Color(0.95, 0.2, 0.2), true)
	if not has_codes:
		draw_rect(codes_rect, Color(0.2, 0.9, 0.95), true)

	draw_rect(terminal_rect, Color(0.65, 0.8, 0.2), true)
	draw_rect(extraction_rect, Color(0.85, 0.85, 0.25), false, 3.0)
	draw_rect(player_rect(), Color(0.95, 0.95, 0.98), true)

	var f := ThemeDB.fallback_font
	if f:
		var status := "Bomb:%s  Codes:%s  Defused:%s" % [bool_str(has_bomb), bool_str(has_codes), bool_str(bomb_defused)]
		draw_string(f, Vector2(24, 34), status, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color.WHITE)
		draw_string(f, Vector2(24, 62), "Timer: %.1fs" % mission_time, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color(1, 0.85, 0.35))
		draw_string(f, Vector2(24, 90), "Move: ←/→   Jump: Enter   Interact/Defuse: Space", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color(0.9, 0.9, 0.9))

		if game_over:
			var msg := "MISSION COMPLETE" if win else "MISSION FAILED"
			draw_string(f, Vector2(460, 260), msg, HORIZONTAL_ALIGNMENT_LEFT, -1, 44, Color(1, 0.95, 0.55))
			draw_string(f, Vector2(430, 300), "Press Enter to restart", HORIZONTAL_ALIGNMENT_LEFT, -1, 24, Color.WHITE)

func bool_str(v: bool) -> String:
	return "yes" if v else "no"

func reset_game() -> void:
	player_pos = Vector2(80, 560)
	player_vel = Vector2.ZERO
	on_ground = false
	has_bomb = false
	has_codes = false
	bomb_armed = false
	bomb_defused = false
	can_extract = false
	mission_time = 120.0
	game_over = false
	win = false
	queue_redraw()
