import arcade
import pymunk
import math
import random
from arcade import Text


class TowerTetris(arcade.Window):
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    SCREEN_TITLE = "Tower Tetris"
    def __init__(self):
        super().__init__(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.SCREEN_TITLE)
        arcade.set_background_color(arcade.color.AMAZON)
        self.space = None
        self.block_shapes = [
            # Rectangle
            [(-20, -10), (20, -10), (20, 10), (-20, 10)],
            # L-shape
            [(-20, -20), (20, -20), (20, 0), (0, 0), (0, 20), (-20, 20)],
            # Penthouse-like
            [(-15, -15), (15, -15), (15, 15), (-15, 15), (-10, 10), (10, 10), (10, 20), (-10, 20)],
            # 
            [(-20, -10), (0, -10), (0, 10), (20, 10), (20, 20), (-20, 20)], #
            [(-15, -15), (15, -15), (15, 15), (-15, 15), (-5, 5), (5, 5), (5, 15), (-5, 15)],
            [(-25, -10), (25, -10), (25, 10), (0, 10), (0, 20), (-25, 20)],
            [(-20, -20), (20, -20), (20, 0), (0, 0), (0, 10), (-20, 10)],
            [(-20, -20), (20, -20), (20, 0), (10, 0), (10, 20), (-20, 20)],

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
        self.setup()

    def setup(self):
        self.space = pymunk.Space()
        self.space.gravity = (0, -200)  # Slower gravity

        # Ground
        wall_thickness = 20
        ground_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        ground_shape = pymunk.Segment(ground_body, (wall_thickness, 0), (self.SCREEN_WIDTH - wall_thickness, 0), wall_thickness)
        ground_shape.color = arcade.color.WHITE
        ground_shape.friction = 1.0  # High friction for ground
        self.space.add(ground_body, ground_shape)

        # Side walls
        left_wall = pymunk.Body(body_type=pymunk.Body.STATIC)
        left_shape = pymunk.Segment(left_wall, (0, 0), (0, self.SCREEN_HEIGHT + 100), wall_thickness)
        left_shape.color = arcade.color.WHITE
        self.space.add(left_wall, left_shape)

        right_wall = pymunk.Body(body_type=pymunk.Body.STATIC)
        right_shape = pymunk.Segment(right_wall, (self.SCREEN_WIDTH, 0), (self.SCREEN_WIDTH, self.SCREEN_HEIGHT + 100), wall_thickness)
        right_shape.color = arcade.color.WHITE
        self.space.add(right_wall, right_shape)

        self.time_since_last_land = 0.0
        self.spawn_block()  # Initial immediate spawn

        self.score_text = Text(f"Score: {self.score}", 10, self.SCREEN_HEIGHT - 20, arcade.color.WHITE, 16)
        self.game_over_text = Text("Game Over! Press ESC to close.", self.SCREEN_WIDTH/2, self.SCREEN_HEIGHT/2,
                                   arcade.color.RED, 30, anchor_x="center")

    def create_block(self, position):
        shape_index = random.choice(range(len(self.block_shapes)))
        verts = self.block_shapes[shape_index]
        body = pymunk.Body()
        body.position = position
        shape = pymunk.Poly(body, verts)
        shape.mass = 1
        r = min(100 + shape_index * 50, 255)
        g = min(int(150 + shape_index ** 1.5), 255)
        b = min(255 - shape_index * 30, 255)
        shape.color = (r, g, b, 255)
        shape.user_data = {'index': shape_index}
        shape.friction = 0.8  # Add friction to help blocks stay in place
        self.space.add(body, shape)
        return body, shape

    def spawn_block(self):
        if self.falling_block:
            return
        self.falling_block = self.create_block((self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT - 50))
        self.falling_block[0].velocity = (0, 0)  # Start with zero velocity for control

    def draw_pymunk(self):
        """Draw all Pymunk shapes"""
        for shape in self.space.shapes:
            if isinstance(shape, pymunk.Segment):
                arcade.draw_line(shape.a.x, shape.a.y, shape.b.x, shape.b.y, shape.color, 3)
            elif isinstance(shape, pymunk.Poly):
                # Get local vertices
                local_verts = shape.get_vertices()
                # Transform to world
                world_verts = [(v.rotated(shape.body.angle) + shape.body.position) for v in local_verts]
                arcade.draw_polygon_filled([(v.x, v.y) for v in world_verts], shape.color)

    def on_key_press(self, key, modifiers):
        self.keys_pressed.add(key)
        if self.falling_block:
            if key == arcade.key.UP:
                body = self.falling_block[0]
                body.angle += math.pi / 2  # Rotate 90 degrees
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
                if abs(body.velocity.y) < 3 and abs(body.velocity.x) < 3:  # Considered landed
                    self.on_landing(body)

            # Game over check
            for dynamic_shape in self.dynamic_shapes[1:]:
                # Convert to world coordinates
                world_verts = [(v.rotated(dynamic_shape.body.angle) + dynamic_shape.body.position) for v in dynamic_shape.get_vertices()]
                # Bottom y-coordinate
                bottom_y = min(v.y for v in world_verts)
                if bottom_y < 20:
                    self.game_over = True
                    break

    def on_draw(self):
        self.clear()  # Replace start_render
        if not self.game_over:
            self.draw_pymunk()
            self.score_text.draw()
        else:
            self.game_over_text.draw()
    
    def on_landing(self, landed_body : pymunk.Body):
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

if __name__ == "__main__":
    window = TowerTetris()
    arcade.run()
