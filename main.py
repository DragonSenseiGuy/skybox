import arcade
import pymunk
from pymunk.autogeometry import convex_decomposition
import math
import random
from arcade import Text
import os
import pyglet
import pyfxr


class TowerTetris(arcade.Window):
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    SCREEN_TITLE = "Tower Tetris"
    BLOCK_SCALE = 1.8
    def __init__(self):
        super().__init__(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.SCREEN_TITLE, resizable=True)
        arcade.set_background_color(arcade.color.AMAZON)
        base_dir = os.path.dirname(__file__)
        bg_path = os.path.join(base_dir, "assets", "images", "city_pixel_bg.png")
        self.bg_texture = None
        self.bg_sprites = arcade.SpriteList()
        self.COL_BLOCK = 1
        self.COL_DEATH = 2
        self.bg_scale_mode = "cover"  # 'stretch' | 'cover' | 'contain'
        if not os.path.exists(bg_path):
            print(f"[background] File not found: {bg_path}")
        else:
            try:
                # Load texture so we can query original size for scaling
                self.bg_texture = arcade.load_texture(bg_path)
                bg_sprite = arcade.Sprite(bg_path)
                bg_sprite.center_x = self.SCREEN_WIDTH / 2
                bg_sprite.center_y = self.SCREEN_HEIGHT / 2
                tex_w = bg_sprite.texture.width if bg_sprite.texture else self.SCREEN_WIDTH
                tex_h = bg_sprite.texture.height if bg_sprite.texture else self.SCREEN_HEIGHT
                if self.bg_scale_mode == "stretch":
                    bg_sprite.width = self.SCREEN_WIDTH
                    bg_sprite.height = self.SCREEN_HEIGHT
                elif self.bg_scale_mode == "cover":
                    factor = max(self.SCREEN_WIDTH / tex_w, self.SCREEN_HEIGHT / tex_h) if tex_w and tex_h else 1.0
                    bg_sprite.width = tex_w * factor
                    bg_sprite.height = tex_h * factor
                else:
                    factor = min(self.SCREEN_WIDTH / tex_w, self.SCREEN_HEIGHT / tex_h) if tex_w and tex_h else 1.0
                    bg_sprite.width = tex_w * factor
                    bg_sprite.height = tex_h * factor
                self.bg_sprites.append(bg_sprite)
                print(f"[background] Loaded: {bg_path}")
            except Exception as e:
                print(f"[background] Failed to load {bg_path}: {e}")
                self.bg_texture = None
        self.space = None
        self.block_shapes = [
            # Rectangle
            [(-20, -10), (20, -10), (20, 10), (-20, 10), (-20, -10)],
            # L-shape
            [(-20, -20), (20, -20), (20, 0), (0, 0), (0, 20), (-20, 20), (-20, -20)],
            # Penthouse-like
            [(-15, -15), (15, -15), (15, 15), (-15, 15), (-10, 10), (10, 10), (10, 20), (-10, 20), (-15, -15)],
            # T-shape
            [(-10, -10), (10, -10), (0, 10), (-10, 10), (10, 10), (-10, -10)],

        ]
        self.falling_block = None
        self.keys_pressed = set()
        self.score = 0
        self.last_shape_index = None
        self.combo_multiplier = 1
        self.game_over = False
        self.score_text = None
        self.game_over_text = None
        self.blocks_placed = 0
        self.spawn_delay = 2.0
        self.time_since_last_land = 0.0
        self._bg_debug_printed = False
        self._init_audio()
        self._active_collisions = set()
        self.setup()

    def _update_background_scale(self, width: int, height: int):
        # Recenter and scale background sprite to fill the window using the selected mode
        if getattr(self, "bg_sprites", None) and len(self.bg_sprites) > 0:
            bg = self.bg_sprites[0]
            bg.center_x = width / 2
            bg.center_y = height / 2
            tex_w = bg.texture.width if bg.texture else width
            tex_h = bg.texture.height if bg.texture else height
            if self.bg_scale_mode == "stretch":
                bg.width = width
                bg.height = height
            elif self.bg_scale_mode == "cover":
                factor = max((width / tex_w) if tex_w else 1.0, (height / tex_h) if tex_h else 1.0)
                bg.width = tex_w * factor
                bg.height = tex_h * factor
            else:  # contain
                factor = min((width / tex_w) if tex_w else 1.0, (height / tex_h) if tex_h else 1.0)
                bg.width = tex_w * factor
                bg.height = tex_h * factor

    def on_resize(self, width: int, height: int):
        # Update window metrics
        self.SCREEN_WIDTH = int(width)
        self.SCREEN_HEIGHT = int(height)
        # Move texts to correct positions
        if self.score_text:
            self.score_text.y = self.SCREEN_HEIGHT - 20
        if self.game_over_text:
            self.game_over_text.x = self.SCREEN_WIDTH / 2
            self.game_over_text.y = self.SCREEN_HEIGHT / 2
        # Update background
        self._update_background_scale(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        # Let Arcade handle the rest
        return super().on_resize(width, height)

    def setup(self):
        self.space = pymunk.Space()
        self.space.gravity = (0, -200)  # Slower gravity

        # Ground
        wall_thickness = 20
        ground_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        ground_shape = pymunk.Segment(ground_body, (wall_thickness, 0), (self.SCREEN_WIDTH - wall_thickness, 0), wall_thickness)
        ground_shape.friction = 1.0  # High friction for ground
        ground_shape.user_data = {'color': arcade.color.WHITE}
        self.space.add(ground_body, ground_shape)

        # Side walls
        left_wall = pymunk.Body(body_type=pymunk.Body.STATIC)
        left_shape = pymunk.Segment(left_wall, (0, 0), (0, self.SCREEN_HEIGHT + 100), wall_thickness)
        left_shape.user_data = {'color': arcade.color.WHITE}
        self.space.add(left_wall, left_shape)

        right_wall = pymunk.Body(body_type=pymunk.Body.STATIC)
        right_shape = pymunk.Segment(right_wall, (self.SCREEN_WIDTH, 0), (self.SCREEN_WIDTH, self.SCREEN_HEIGHT + 100), wall_thickness)
        right_shape.user_data = {'color': arcade.color.WHITE}
        self.space.add(right_wall, right_shape)

        # Death sensor below the screen to detect falling blocks
        death_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        death_shape = pymunk.Segment(death_body, (-1000, -150), (self.SCREEN_WIDTH + 1000, -150), 1)
        death_shape.sensor = True
        death_shape.collision_type = self.COL_DEATH
        death_shape.user_data = {'sensor': True}
        self.space.add(death_body, death_shape)

        # Collision handler: block hits death sensor -> game over
        handler = self.space.add_collision_handler(self.COL_BLOCK, self.COL_DEATH)
        handler.begin = self._on_block_hits_death

        # Collision handler: blocks colliding with each other -> play hit sounds
        hit_handler = self.space.add_collision_handler(self.COL_BLOCK, self.COL_BLOCK)
        # Use post_solve so we can read the collision impulse and respond after physics
        hit_handler.post_solve = self._on_blocks_collide
        # Use separate to clear active collision flag so future collisions will play again
        hit_handler.separate = self._on_blocks_separate

        self.time_since_last_land = 0.0
        self.spawn_block()  # Initial immediate spawn

        self.score_text = Text(f"Score: {self.score}", 10, self.SCREEN_HEIGHT - 20, arcade.color.WHITE, 16)
        self.game_over_text = Text("Game Over! Press ESC to close.", self.SCREEN_WIDTH/2, self.SCREEN_HEIGHT/2,
                                   arcade.color.RED, 30, anchor_x="center")

    def create_block(self, position):
        shape_index = random.choice(range(len(self.block_shapes)))
        base_verts = self.block_shapes[shape_index]
        scale = self.BLOCK_SCALE
        scaled_verts = [(float(x) * scale, float(y) * scale) for (x, y) in base_verts]
        convex_shapes_verts = convex_decomposition(scaled_verts, 0)
        body = pymunk.Body()
        body.position = position
        self.space.add(body)
        r = min(100 + shape_index * 50, 255)
        g = min(int(150 + shape_index ** 1.5), 255)
        b = min(255 - shape_index * 30, 255)
        for verts in convex_shapes_verts:
            shape = pymunk.Poly(body, verts)
            shape.density = self.BLOCK_SCALE ** 2
            shape.user_data = {'index': shape_index, 'color': (r, g, b, 255)}
            shape.friction = 0.8  # Add friction to help blocks stay in place
            shape.collision_type = self.COL_BLOCK
            self.space.add(shape)
        return body, shape

    def spawn_block(self):
        if self.falling_block:
            return
        self.falling_block = self.create_block((self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT - 50))
        self.falling_block[0].velocity = (0, 0)  # Start with zero velocity for control
        self._play_sfx('spawn')

    def draw_pymunk(self):
        """Draw all Pymunk shapes"""
        for shape in self.space.shapes:
            if isinstance(shape, pymunk.Segment):
                # Skip invisible/sensor segments like the death line
                if getattr(shape, "sensor", False) or (getattr(shape, "user_data", None) and shape.user_data.get("sensor")):
                    continue
                color = (shape.user_data.get('color') if getattr(shape, "user_data", None) else arcade.color.WHITE)
                arcade.draw_line(shape.a.x, shape.a.y, shape.b.x, shape.b.y, color, 3)
            elif isinstance(shape, pymunk.Poly):
                # Get local vertices
                local_verts = shape.get_vertices()
                # Transform to world
                world_verts = [(v.rotated(shape.body.angle) + shape.body.position) for v in local_verts]
                color = (shape.user_data.get('color') if getattr(shape, "user_data", None) else arcade.color.WHITE)
                arcade.draw_polygon_filled([(v.x, v.y) for v in world_verts], color)

    def on_key_press(self, key, modifiers):
        self.keys_pressed.add(key)

        # Global shortcuts
        if key == arcade.key.F:
            # Toggle fullscreen and update background scale to new size
            self.set_fullscreen(not self.fullscreen)
            w, h = self.get_size()
            self.on_resize(w, h)
        elif key == arcade.key.S:
            # Cycle background scale mode: stretch -> cover -> contain
            modes = ("stretch", "cover", "contain")
            try:
                idx = modes.index(self.bg_scale_mode)
            except ValueError:
                idx = 0
            self.bg_scale_mode = modes[(idx + 1) % len(modes)]
            print(f"[background] scale mode: {self.bg_scale_mode}")
            self._update_background_scale(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)

        # Gameplay controls
        if self.falling_block:
            if key == arcade.key.UP:
                body = self.falling_block[0]
                body.angle += math.pi / 2  # Rotate 90 degrees
                self._play_sfx('rotate')
    def on_key_hold(self, key):
        if self.falling_block:
            if key == arcade.key.RIGHT:
                body = self.falling_block[0]
                vx = min(200, body.velocity.x + 20) # adds velocity up to a certain point
                body.velocity = (vx, body.velocity.y)

            elif key == arcade.key.LEFT:
                body = self.falling_block[0]
                vx = body.velocity.x
                vx = max(-200, vx - 20) # adds velocity up to a certain point
                body.velocity = (vx, body.velocity.y)
            elif key == arcade.key.SPACE:
                body = self.falling_block[0]
                body.velocity = (0, max(-500, body.velocity.y - 100))  # Fast drop straight down
                self.keys_pressed.discard(arcade.key.LEFT)
                self.keys_pressed.discard(arcade.key.RIGHT)

    def on_key_release(self, key, modifiers):
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)

    def on_update(self, delta_time):
        if not self.game_over:
            # Spawn new block after delay since last land, if no current falling block
            if self.time_since_last_land >= self.spawn_delay and not self.falling_block:
                self.spawn_block()
                # Adjust delay every 10 blocks (after spawning, based on placed)
                if self.blocks_placed % 10 == 0 and self.blocks_placed > 0:
                    self.spawn_delay = max(0.5, self.spawn_delay - 0.2)
            #else:
            #    print(f"Time since last land: {self.time_since_last_land:.2f}s, Spawn delay: {self.spawn_delay:.2f}s")
            temp_keys = self.keys_pressed.copy()
            for key in temp_keys:
                self.on_key_hold(key)
            self.time_since_last_land += delta_time

            # Apply input to falling block before physics
            #if self.falling_block:
            #    body = self.falling_block[0]
            #    vx = 0
            #    if arcade.key.LEFT in self.keys_pressed:
            #        vx = -150
            #    elif arcade.key.RIGHT in self.keys_pressed:
            #        vx = 150
            #    body.velocity = (vx, body.velocity.y)

            # Step physics simulation
            if self.space:
                self.space.step(delta_time)

            # Check for landing after physics step
            if self.falling_block:
                body = self.falling_block[0]
                velocity_x = abs(body.velocity.x)
                velocity_x = max(0, velocity_x - 5)  # Friction effect
                body.velocity = (math.copysign(velocity_x, body.velocity.x), body.velocity.y)
                self.falling_block = (body, self.falling_block[1])
                if abs(body.velocity.y) < 3:  # Considered landed
                    self.on_landing(body)

            # Game over handled by death sensor collision

    def _on_block_hits_death(self, arbiter, space, data):
        # Trigger game over when any block hits the death sensor
        try:
            self._play_sfx('game_over')
        except Exception:
            pass
        self.game_over = True
        return True

    def _on_blocks_collide(self, arbiter, space, data):
        # Called after two block shapes collide. Play the hit sound only once per contact.
        try:
            # Identify the two shapes involved and create a stable key for the pair
            shapes = getattr(arbiter, "shapes", None)
            if not shapes or len(shapes) < 2:
                return True
            key = tuple(sorted((id(shapes[0]), id(shapes[1]))))
            # If we've already played a sound for this active contact, skip
            if key in self._active_collisions:
                return True
            # Mark this contact as active so further post_solve calls for the same contact don't replay
            self._active_collisions.add(key)

            # Attempt to read collision impulse to set volume
            impulse_vec = getattr(arbiter, "total_impulse", None)
            if impulse_vec is None:
                # No impulse available -> use a small default
                impulse = 0.0
            else:
                # Try to get a length; fallback to converting to float
                impulse = 0.0
                try:
                    impulse = float(getattr(impulse_vec, "length", impulse_vec))
                except Exception:
                    try:
                        impulse = float(impulse_vec)
                    except Exception:
                        impulse = 0.0

            # Map impulse to volume: choose a sensible scale factor and clamp
            volume = max(0.05, min(1.0, impulse / 150.0))
            snd = self.sfx.get('hit') if hasattr(self, "sfx") else None
            if snd:
                player = snd.play()
                try:
                    player.volume = volume
                except Exception:
                    # Some players may not support volume; ignore
                    pass
        except Exception as e:
            print(f"[audio] collision play error: {e}")
        # Return True to allow normal physics resolution to continue
        return True

    def _on_blocks_separate(self, arbiter, space, data):
        # Called when two block shapes separate. Clear the active flag so future collisions between
        # the same shapes will play sound again.
        try:
            shapes = getattr(arbiter, "shapes", None)
            if not shapes or len(shapes) < 2:
                return None
            key = tuple(sorted((id(shapes[0]), id(shapes[1]))))
            self._active_collisions.discard(key)
        except Exception:
            # Ignore errors here; separation cleanup is best-effort
            pass
        return None

    def on_draw(self):
        self.clear()  # Replace start_render
        if getattr(self, "bg_sprites", None) and len(self.bg_sprites) > 0:
            if not getattr(self, "_bg_debug_printed", True):
                print(f"[background] drawing {len(self.bg_sprites)} sprite(s)")
                self._bg_debug_printed = True
            self.bg_sprites.draw()
        else:
            if not getattr(self, "_bg_debug_printed", True):
                print("[background] no background sprites; drawing solid color")
                self._bg_debug_printed = True
            arcade.draw_lrbt_rectangle_filled(0, self.SCREEN_WIDTH, 0, self.SCREEN_HEIGHT, arcade.color.BLACK)
        if not self.game_over:
            self.draw_pymunk()
        else:
            self.game_over_text.draw()
        self.score_text.draw()

    def on_landing(self, landed_body : pymunk.Body):
        self._play_sfx('land')
        shape_index = self.falling_block[1].user_data['index']
        base_score = 10
        if abs(landed_body.position.x - self.SCREEN_WIDTH / 2) < 30:
            base_score += 20  # Centered bonus
        if shape_index == self.last_shape_index and self.last_shape_index != None:
            self.combo_multiplier += 0.5
        else:
            self.combo_multiplier = 1.0
        self.score += int(base_score * self.combo_multiplier)
        self.last_shape_index = shape_index
        self.blocks_placed += 1
        self.falling_block = None
        self.time_since_last_land = 0.0  # Reset timer for next spawn delay
        self.score_text.text = f"Score: {self.score}"


    def fix_body(self, dynamic_body : pymunk.Body):
        """Convert a dynamic body to static, preserving its shape and position.

        this function is useless now since I found out we can just add friction on shapes
        """

        shape = list(dynamic_body.shapes)[0]
        self.space.shapes.remove(shape)
        self.space.remove(dynamic_body)

        static_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        static_body.position = dynamic_body.position

        static_shape = pymunk.Poly(static_body, shape.get_vertices())
        static_shape.mass = 1
        static_shape.color = shape.color
        static_shape.user_data = shape.user_data
        self.space.add(static_body, static_shape)


    @property
    def dynamic_bodies(self):
        return [body for body in self.space.bodies if isinstance(body, pymunk.Body) and body.body_type != pymunk.Body.STATIC]

    def _init_audio(self):
        try:
            self.sfx = {
                'spawn': pyglet.media.StaticSource(pyfxr.explosion()),
                'rotate': pyglet.media.StaticSource(pyfxr.explosion()),
                'land': pyglet.media.StaticSource(pyfxr.explosion()),
                'game_over': pyglet.media.StaticSource(pyfxr.explosion()),
                # Hit sound for block-block collisions; small percussive pickup works well
                'hit': pyglet.media.StaticSource(pyfxr.explosion()),
            }
            print("[audio] pyfxr sounds initialized")
        except Exception as e:
            print(f"[audio] init error: {e}")
            self.sfx = {}

    def _play_sfx(self, name: str):
        try:
            snd = self.sfx.get(name) if hasattr(self, "sfx") else None
            if snd:
                snd.play()
        except Exception as e:
            print(f"[audio] play error for {name}: {e}")

if __name__ == "__main__":
    window = TowerTetris()
    arcade.run()
