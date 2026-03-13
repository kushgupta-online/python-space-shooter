import arcade
import math
import random

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Space Shooter"

PLAYER_SPEED = 5
PLAYER_MAX_HEALTH = 100

BULLET_SPEED = 10
PLAYER_BULLET_DAMAGE = 25
ENEMY_BULLET_DAMAGE = 10

ENEMY_SPEED = 2
ENEMY_MAX_HEALTH = 50
ENEMY_FIRE_RATE = 1.2

FAST_ENEMY_SPEED = 4
FAST_ENEMY_HEALTH = 30
FAST_ENEMY_FIRE_RATE = 0.8

TANK_ENEMY_SPEED = 1
TANK_ENEMY_HEALTH = 120
TANK_ENEMY_FIRE_RATE = 2.0

BOSS_HEALTH = 400
BOSS_SPEED = 1.2
BOSS_FIRE_RATE = 0.6

SPAWN_RATE = 2.0

POWERUP_TYPES = ["health", "rapid", "shield"]
POWERUP_FALL_SPEED = 2


class GameWindow(arcade.Window):

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        
        # --- BACKGROUND ---
        self.background_list = arcade.SpriteList()
        self.background_sprite = arcade.Sprite("space_bg.png")
        self.background_sprite.center_x = SCREEN_WIDTH // 2
        self.background_sprite.center_y = SCREEN_HEIGHT // 2
        self.background_sprite.width = SCREEN_WIDTH
        self.background_sprite.height = SCREEN_HEIGHT
        self.background_list.append(self.background_sprite)
        
        # --- SPRITE LISTS ---
        self.player_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()
        self.powerup_list = arcade.SpriteList()
        
        # --- NEW CODE: Bullet Sprite Lists ---
        self.player_bullet_list = arcade.SpriteList()
        self.enemy_bullet_list = arcade.SpriteList()
        
        self.reset_game()

    # ---------------- RESET GAME ---------------- #

    def reset_game(self):

        self.player_x = SCREEN_WIDTH // 2
        self.player_y = SCREEN_HEIGHT // 2
        self.player_angle = 0

        self.player_health = PLAYER_MAX_HEALTH
        self.score = 0
        self.game_over = False

        self.keys_pressed = set()
        self.player_bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.powerups = []

        self.spawn_timer = 0
        self.shooting = False
        self.shoot_timer = 0
        self.fire_rate = 0.2

        self.rapid_fire_timer = 0
        self.invincible_timer = 0

        self.boss = None
        self.boss_round = 0
        self.next_boss_score = 100

        # --- INITIALIZE SPRITES ---
        self.player_list.clear()
        self.enemy_list.clear()
        self.powerup_list.clear()
        self.player_bullet_list.clear() # Clear bullets on restart
        self.enemy_bullet_list.clear()
        
        self.player_sprite = arcade.Sprite("player_ship.png", scale=0.15) 
        self.player_list.append(self.player_sprite)

    # ---------------- DRAW ---------------- #

    def on_draw(self):
        self.clear()

        self.background_list.draw()

        if self.game_over:
            arcade.draw_text("GAME OVER", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40, arcade.color.RED, 40, anchor_x="center")
            arcade.draw_text(f"Final Score: {self.score}", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, arcade.color.WHITE, 20, anchor_x="center")
            arcade.draw_text("Press R to Restart", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50, arcade.color.YELLOW, 18, anchor_x="center")
            return

        # Draw all sprites
        self.player_list.draw()
        self.enemy_list.draw()
        self.powerup_list.draw()
        
        # --- NEW CODE: Draw the bullet images ---
        self.player_bullet_list.draw()
        self.enemy_bullet_list.draw()

        if self.invincible_timer > 0:
            arcade.draw_circle_outline(self.player_x, self.player_y, 45, arcade.color.BLUE, 3)

        self.draw_health_bar(self.player_x, self.player_y - 40, 60, 6, self.player_health, PLAYER_MAX_HEALTH)

        for enemy in self.enemies:
            self.draw_health_bar(enemy["x"], enemy["y"] - 35, 40, 5, enemy["health"], enemy["max_health"])

        if self.boss:
            self.draw_health_bar(self.boss["x"], self.boss["y"] - 80, 120, 10, self.boss["health"], self.boss["max_health"])

        arcade.draw_text(f"Score: {self.score}", 20, SCREEN_HEIGHT - 30, arcade.color.WHITE, 16)

    # ---------------- UPDATE ---------------- #

    def on_update(self, delta_time):

        if self.game_over:
            return

        if arcade.key.W in self.keys_pressed: self.player_y += PLAYER_SPEED
        if arcade.key.S in self.keys_pressed: self.player_y -= PLAYER_SPEED
        if arcade.key.A in self.keys_pressed: self.player_x -= PLAYER_SPEED
        if arcade.key.D in self.keys_pressed: self.player_x += PLAYER_SPEED

        self.player_x = max(0, min(SCREEN_WIDTH, self.player_x))
        self.player_y = max(0, min(SCREEN_HEIGHT, self.player_y))
        
        self.player_sprite.center_x = self.player_x
        self.player_sprite.center_y = self.player_y
        self.player_sprite.angle = self.player_angle - 90

        if self.shooting:
            self.shoot_timer += delta_time
            if self.shoot_timer >= self.fire_rate:
                self.fire_player_bullet()
                self.shoot_timer = 0

        self.spawn_timer += delta_time
        if self.spawn_timer >= SPAWN_RATE and self.boss is None:
            self.spawn_enemy()
            self.spawn_timer = 0

        if self.score >= self.next_boss_score and self.boss is None:
            self.spawn_boss()
            self.next_boss_score += 100

        self.update_player_bullets()
        self.update_enemies(delta_time)
        self.update_enemy_bullets()
        self.update_powerups(delta_time)
        self.update_boss(delta_time)

        if self.player_health <= 0:
            self.game_over = True

    # ---------------- PLAYER BULLETS ---------------- #

    def fire_player_bullet(self):

        angle_rad = math.radians(self.player_angle)
        nose_offset = 35 
        
        spawn_x = self.player_x + math.cos(angle_rad) * nose_offset
        spawn_y = self.player_y + math.sin(angle_rad) * nose_offset

        # --- NEW CODE: Create player laser sprite ---
        laser_sprite = arcade.Sprite("player_laser.png", scale=0.05) # Adjust scale as needed
        laser_sprite.center_x = spawn_x
        laser_sprite.center_y = spawn_y
        laser_sprite.angle = self.player_angle
        
        self.player_bullet_list.append(laser_sprite)

        self.player_bullets.append(
            {
                "x": spawn_x,
                "y": spawn_y,
                "dx": math.cos(angle_rad) * BULLET_SPEED,
                "dy": math.sin(angle_rad) * BULLET_SPEED,
                "sprite": laser_sprite # Link sprite to dictionary
            }
        )

    # ---------------- PLAYER BULLET UPDATE ---------------- #

    def update_player_bullets(self):

        for bullet in self.player_bullets:
            bullet["x"] += bullet["dx"]
            bullet["y"] += bullet["dy"]
            
            # --- NEW CODE: Sync laser sprite movement ---
            bullet["sprite"].center_x = bullet["x"]
            bullet["sprite"].center_y = bullet["y"]

            for enemy in self.enemies:
                if math.hypot(bullet["x"] - enemy["x"], bullet["y"] - enemy["y"]) < 20:
                    enemy["health"] -= PLAYER_BULLET_DAMAGE
                    bullet["hit"] = True
                    break

            if self.boss:
                if math.hypot(bullet["x"] - self.boss["x"], bullet["y"] - self.boss["y"]) < 60:
                    self.boss["health"] -= PLAYER_BULLET_DAMAGE
                    bullet["hit"] = True

        # --- NEW CODE: Clean up hit/offscreen bullet sprites ---
        alive_bullets = []
        for b in self.player_bullets:
            if 0 < b["x"] < SCREEN_WIDTH and 0 < b["y"] < SCREEN_HEIGHT and not b.get("hit"):
                alive_bullets.append(b)
            else:
                b["sprite"].remove_from_sprite_lists() # Remove the image
                
        self.player_bullets = alive_bullets

        for enemy in self.enemies[:]:
            if enemy["health"] <= 0:
                if random.random() < 0.3:
                    self.spawn_powerup(enemy["x"], enemy["y"])

                enemy["sprite"].remove_from_sprite_lists()
                self.enemies.remove(enemy)
                self.score += 10

    # ---------------- ENEMY SPAWN ---------------- #

    def spawn_enemy(self):

        side = random.choice(["left", "right", "top", "bottom"])
        enemy_type = random.choice(["normal", "fast", "tank"])

        if side == "left": x, y = 0, random.randint(0, SCREEN_HEIGHT)
        elif side == "right": x, y = SCREEN_WIDTH, random.randint(0, SCREEN_HEIGHT)
        elif side == "top": x, y = random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT
        else: x, y = random.randint(0, SCREEN_HEIGHT), 0

        if enemy_type == "fast":
            health, speed, fire_rate = FAST_ENEMY_HEALTH, FAST_ENEMY_SPEED, FAST_ENEMY_FIRE_RATE
            enemy_sprite = arcade.Sprite("enemy_fast.png", scale=0.1)
        elif enemy_type == "tank":
            health, speed, fire_rate = TANK_ENEMY_HEALTH, TANK_ENEMY_SPEED, TANK_ENEMY_FIRE_RATE
            enemy_sprite = arcade.Sprite("enemy_tank.png", scale=0.15)
        else:
            health, speed, fire_rate = ENEMY_MAX_HEALTH, ENEMY_SPEED, ENEMY_FIRE_RATE
            enemy_sprite = arcade.Sprite("enemy_normal.png", scale=0.15)

        self.enemy_list.append(enemy_sprite)

        self.enemies.append(
            {
                "x": x, "y": y,
                "health": health, "max_health": health,
                "speed": speed, "fire_rate": fire_rate,
                "shoot_timer": 0, "angle": 0,
                "type": enemy_type,
                "sprite": enemy_sprite
            }
        )

    # ---------------- ENEMY UPDATE ---------------- #

    def update_enemies(self, delta_time):

        for enemy in self.enemies:
            dx = self.player_x - enemy["x"]
            dy = self.player_y - enemy["y"]
            angle = math.atan2(dy, dx)

            enemy["angle"] = math.degrees(angle)
            enemy["x"] += math.cos(angle) * enemy["speed"]
            enemy["y"] += math.sin(angle) * enemy["speed"]
            
            enemy["sprite"].center_x = enemy["x"]
            enemy["sprite"].center_y = enemy["y"]
            enemy["sprite"].angle = enemy["angle"] - 90

            enemy["shoot_timer"] += delta_time

            if enemy["shoot_timer"] >= enemy["fire_rate"]:
                # --- CHANGED: Passing rotation angle to the firing method ---
                self.spawn_enemy_bullet(enemy["x"], enemy["y"], angle, 6)
                enemy["shoot_timer"] = 0

            if math.hypot(enemy["x"] - self.player_x, enemy["y"] - self.player_y) < 30:
                if self.invincible_timer <= 0:
                    if enemy["type"] == "fast": self.player_health -= 15
                    elif enemy["type"] == "tank": self.player_health -= 35
                    else: self.player_health -= 20
                enemy["health"] = 0

    # ---------------- BOSS ---------------- #

    def spawn_boss(self):

        self.boss_round += 1
        boss_sprite = arcade.Sprite("boss_ship.png", scale=0.5)
        self.enemy_list.append(boss_sprite)

        self.boss = {
            "x": SCREEN_WIDTH // 2,
            "y": SCREEN_HEIGHT + 80,
            "health": BOSS_HEALTH + self.boss_round * 80,
            "max_health": BOSS_HEALTH + self.boss_round * 80,
            "shoot_timer": 0,
            "pattern_angle": 0,
            "sprite": boss_sprite 
        }

    def update_boss(self, delta_time):

        if not self.boss:
            return

        dx = self.player_x - self.boss["x"]
        dy = self.player_y - self.boss["y"]
        angle = math.atan2(dy, dx)

        self.boss["x"] += math.cos(angle) * BOSS_SPEED
        self.boss["y"] += math.sin(angle) * BOSS_SPEED
        
        self.boss["sprite"].center_x = self.boss["x"]
        self.boss["sprite"].center_y = self.boss["y"]
        self.boss["sprite"].angle = math.degrees(angle) - 90

        if math.hypot(self.boss["x"] - self.player_x, self.boss["y"] - self.player_y) < 50:
            self.player_health = 0
            self.game_over = True

        self.boss["shoot_timer"] += delta_time

        if self.boss["shoot_timer"] >= BOSS_FIRE_RATE:
            
            # --- CHANGED: Using the new helper method to spawn bullets ---
            if self.boss_round == 1:
                self.spawn_enemy_bullet(self.boss["x"], self.boss["y"], angle, 6)
            elif self.boss_round == 2:
                for spread in [-0.25, 0, 0.25]:
                    self.spawn_enemy_bullet(self.boss["x"], self.boss["y"], angle + spread, 7)
            elif self.boss_round == 3:
                for i in range(12):
                    self.spawn_enemy_bullet(self.boss["x"], self.boss["y"], i * (math.pi * 2 / 12), 4)
            else:
                self.boss["pattern_angle"] += 0.3
                for i in range(6):
                    self.spawn_enemy_bullet(self.boss["x"], self.boss["y"], self.boss["pattern_angle"] + i * (math.pi / 3), 5)
                    
            self.boss["shoot_timer"] = 0

        if self.boss["health"] <= 0:
            self.score += 50
            self.boss["sprite"].remove_from_sprite_lists()
            self.boss = None

    # ---------------- ENEMY BULLETS ---------------- #

    # --- NEW CODE: Helper method to handle creating enemy bullet sprites ---
    def spawn_enemy_bullet(self, x, y, angle_rad, speed):
        
        laser_sprite = arcade.Sprite("enemy_laser.png", scale=0.1)
        laser_sprite.center_x = x
        laser_sprite.center_y = y
        laser_sprite.angle = math.degrees(angle_rad) - 90
        
        self.enemy_bullet_list.append(laser_sprite)
        
        self.enemy_bullets.append(
            {
                "x": x, "y": y,
                "dx": math.cos(angle_rad) * speed,
                "dy": math.sin(angle_rad) * speed,
                "sprite": laser_sprite
            }
        )

    def update_enemy_bullets(self):

        for bullet in self.enemy_bullets:
            bullet["x"] += bullet["dx"]
            bullet["y"] += bullet["dy"]
            
            # Sync image position
            bullet["sprite"].center_x = bullet["x"]
            bullet["sprite"].center_y = bullet["y"]

            if math.hypot(bullet["x"] - self.player_x, bullet["y"] - self.player_y) < 20:
                if self.invincible_timer <= 0:
                    self.player_health -= ENEMY_BULLET_DAMAGE
                bullet["hit"] = True

        # Clean up hit/offscreen bullet sprites
        alive_bullets = []
        for b in self.enemy_bullets:
            if 0 < b["x"] < SCREEN_WIDTH and 0 < b["y"] < SCREEN_HEIGHT and not b.get("hit"):
                alive_bullets.append(b)
            else:
                b["sprite"].remove_from_sprite_lists()
                
        self.enemy_bullets = alive_bullets

    # ---------------- POWERUPS ---------------- #

    def spawn_powerup(self, x, y):

        power_type = random.choice(POWERUP_TYPES)
        sprite_name = f"powerup_{power_type}.png" 
        p_sprite = arcade.Sprite(sprite_name, scale=0.1)
        p_sprite.center_x = x
        p_sprite.center_y = y
        self.powerup_list.append(p_sprite)

        self.powerups.append(
            {"x": x, "y": y, "type": power_type, "dy": -POWERUP_FALL_SPEED, "sprite": p_sprite}
        )

    def update_powerups(self, delta_time):

        for p in self.powerups:

            p["y"] += p["dy"]
            p["sprite"].center_y = p["y"] 

            if math.hypot(self.player_x - p["x"], self.player_y - p["y"]) < 30:

                if p["type"] == "health":
                    self.player_health = min(PLAYER_MAX_HEALTH, self.player_health + 30)
                elif p["type"] == "rapid":
                    self.rapid_fire_timer = 5
                elif p["type"] == "shield":
                    self.invincible_timer = 5

                p["collected"] = True
                p["sprite"].remove_from_sprite_lists() 
            
            elif p["y"] < 0:
                p["sprite"].remove_from_sprite_lists()

        self.powerups = [
            p for p in self.powerups if not p.get("collected") and p["y"] > 0
        ]

        if self.rapid_fire_timer > 0:
            self.rapid_fire_timer -= delta_time
            self.fire_rate = 0.05
        else:
            self.fire_rate = 0.2

        if self.invincible_timer > 0:
            self.invincible_timer -= delta_time

    # ---------------- HEALTH BAR ---------------- #

    def draw_health_bar(self, x, y, width, height, health, max_health):

        health = max(0, health)
        ratio = health / max_health

        arcade.draw_lbwh_rectangle_filled(x - width // 2, y - height // 2, width, height, arcade.color.DARK_GRAY)

        if ratio > 0.6: color = arcade.color.GREEN
        elif ratio > 0.3: color = arcade.color.ORANGE
        else: color = arcade.color.RED

        arcade.draw_lbwh_rectangle_filled(x - width // 2, y - height // 2, width * ratio, height, color)

    # ---------------- INPUT ---------------- #

    def on_key_press(self, key, modifiers):
        if key == arcade.key.R and self.game_over:
            self.reset_game()
            return
        self.keys_pressed.add(key)

    def on_key_release(self, key, modifiers):
        self.keys_pressed.discard(key)

    def on_mouse_motion(self, x, y, dx, dy):
        dx = x - self.player_x
        dy = y - self.player_y
        self.player_angle = math.degrees(math.atan2(dy, dx))

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.shooting = True

    def on_mouse_release(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.shooting = False


def main():
    window = GameWindow()
    arcade.run()


if __name__ == "__main__":
    main()