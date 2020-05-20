import collections
import math
import random
import pygame
from pygame import mixer

# initialise pygame
pygame.init()

# Set caption and icon
pygame.display.set_caption("Tower Defense")
icon = pygame.image.load('purple_tower.png')
pygame.display.set_icon(icon)

# Music
mixer.music.load('bloons_music.mp3')
mixer.music.play(-1)

# set screen
width = 800
height = 600
screen = pygame.display.set_mode((width, height))
square = 25

class Enemy:
    def __init__(self):
        self.value = 50
        self.health = 1000
        self.x = 0     # x,y coords position
        self.y = 100
        self.direction = 0  # 0 east, 1 north, 2 west, 3 south
        self.max_health = 1000
        self.speed = 10
        self.image = pygame.image.load('blob_angry.png')    # load image 
        self.poisoned = False
        self.poisoned_time = 0

    def draw(self,surface):
        """draw enemy unto surface"""
        surface.blit(self.image, (self.x,self.y))
        self.display_health(surface)

    def display_health(self, surface):
        # Display health if damage has been done
        if self.health != self.max_health and self.health >0:
            length = 50 #length of the health bar
            green = length*self.health / self.max_health    #length of green portion
            pygame.draw.rect(surface, (255,0,0), (self.x-13, self.y-20, length, 10), 0) #red
            # Display health as purple if poisoned else green
            if self.poisoned:
                PURPLE = (160,32,240)
                pygame.draw.rect(surface, PURPLE, (self.x-13, self.y - 20, green, 10), 0)
            else:
                pygame.draw.rect(surface, (0, 255, 0), (self.x-13, self.y - 20, green, 10), 0)

    def move(self, path):
        """Move by speed units in its direction"""
        if self.direction == 0:
            self.x += self.speed
        elif self.direction == 1:
            self.y -= self.speed
        elif self.direction == 2:
            self.x -= self.speed
        else:
            self.y += self.speed

        # If a turn is reached change direction
        if (self.x, self.y) in path.vertices:
            self.direction = path.vertices[(self.x,self.y)]

class Blob(Enemy):
    def __init__(self):
        super().__init__()
        self.x = 100
        self.y = 500
        self.health = 69
        self.speed = 10

class Boss(Enemy):
    def __init__(self):
        super().__init__()
        self.max_health = 5000
        self.health = 5000
        self.x = 0
        self.y = 100
        self.speed = 5
        self.image = pygame.image.load('blob_angry.png')

class Tower:
    def __init__(self, X, Y):
        self.x = (X//square)*square
        self.y = (Y//square)*square
        self.name = 'Purple'
        self.level = 1
        self.upgradeCost = 1000
        self.damage = 100
        self.range = 200
        self.cost = 500
        self.image = pygame.image.load('purple_tower.png')
        self.poison = False
        self.projectiles = []
        self.max_reload_time = 10
        self.reload_time = 0

    def upgrade(self):
        if self.level < 9:
            self.level += 1
            self.range *= 1.2
            self.damage *= 1.2
            self.upgradeCost += 200

        if self.level % 2 ==0 :
            self.max_reload_time -= 2

    def draw(self, surface):
        """
        Draw tower on surface
        """
        surface.blit(self.image,(self.x,self.y))
        # If tower upgraded display tower level on tower
        if self.level > 1:
            font = pygame.font.Font('freesansbold.ttf', 20)
            WHITE = (255,255,255)
            level_number = font.render(str(self.level), True, WHITE)
            surface.blit(level_number,(self.x+8,self.y+5))

class PurpleTower(Tower):
    def __init__(self,X,Y):
        super().__init__(X,Y)
        self.name = 'Purple'
        self.damage = 20
        self.range = 100
        self.cost = 500
        self.image = pygame.image.load('purple_tower.png')
        self.poison = True
        self.max_poison_time = 40
        self.max_reload_time = 20
        # overload upgrade increases poison time and poison damage

class OrangeTower(Tower):
    def __init__(self,X,Y):
        super().__init__(X,Y)
        self.name = 'Orange'
        self.damage = 10000
        self.range = 1000
        self.cost = 500
        self.image = pygame.image.load('orange_tower.png')
        self.max_reload_time = 100

class GreenTower(Tower):
    def __init__(self,X,Y):
        super().__init__(X,Y)
        self.name = 'Green'
        self.damage = 20
        self.range = 1000
        self.cost = 500
        self.image = pygame.image.load('green_tower.png')
        self.max_reload_time = 10
        
class Path:
    def __init__(self):
        """
        When a vertex is reached the direction changes to:
        0 east, 1 north, 2 west, 3 south
        """
        self.vertices = {(0,100):0,(100,100):3,(100,500):0,(700,500):1,(700,100):2,(250,100):1,(250,0):1}

    def draw(self, surface):
        pygame.draw.rect(surface, (255, 253, 208), (0,100,100,square))
        pygame.draw.rect(surface, (255, 253, 208), (100,100,square,400))
        pygame.draw.rect(surface, (255, 253, 208), (100,500,600,square))
        pygame.draw.rect(surface, (255, 253, 208), (700,100,square,400+square))
        pygame.draw.rect(surface, (255, 253, 208), (250,100,450,square))
        pygame.draw.rect(surface, (255, 253, 208), (250,0,square,100))

    def click_on_path(self, X, Y):
        # Returns if (X,Y) lies on the path
        X = X//25
        Y = Y//25
        if Y == 4 and X>=0 and X<=4:
            return True
        if X==4 and Y>4 and Y<21:
            return True
        if Y==20 and X>4 and X<29:
            return True
        if X == 28 and Y<20 and Y>3:
            return True
        if Y == 4 and X<28 and X>10:
            return True
        if Y<5 and X==10:
            return True

        return False

class Game:
    def __init__(self):
        self.wave = 1
        self.enemies = []
        self.money = 10000
        self.lives = 2
        self.towers = []
        self.path = Path()
        self.music = True
        self.selected_tower = 1
        self.paused = False
        self.running = True
        self.set_wave_enemies()

    def draw_window(self):
        """Draw onto screen and update"""
        SANDY = (194,178,128)
        screen.fill(SANDY)  # set background to sandy colour
        self.draw(screen)  # draw game state on screen
        pygame.display.update()

    def game_over_message(self):
        # Display game over message with number of waves survived
        message = "GAME OVER! You survived " + str(self.wave-1) + " wave"
        if self.wave == 2:
            message += "."
        else:
            message += "s."
        # Display message in screen centre and then update screen
        font = pygame.font.Font('freesansbold.ttf', 32)
        RED = (255,0,0)
        text = font.render(message, True, RED)
        screen.blit(text,(150,260))
        text2 = font.render("Press N for new game and Q to quit.", True, (0,0,0))
        screen.blit(text2, (150,310))

        pygame.display.update()

        # Wait for user input new game/ quit game
        done = False
        while not done:
            for event in pygame.event.get(): 
                if event.type == pygame.QUIT:
                    self.running = False
                    self.paused = False
                    done = True
                    break
                elif event.type == pygame.KEYDOWN: 
                    if event.key == pygame.K_n: 
                        self = self.__init__()
                        done = True
                        break
                    elif event.key == pygame.K_q:
                        self.running = False
                        self.paused = False
                        done = True
                        break

    def incoming_boss_message(self):
        self.draw_window()
        font = pygame.font.Font('freesansbold.ttf', 64)
        RED = (255,0,0)
        text = font.render("Boss incoming!", True, RED)
        screen.blit(text,(180,260))
        pygame.display.update()
        pygame.time.delay(3000)   # Wait for 3 seconds

    def pause_game(self):
        """Pause game and wait until it is unpaused or quit game"""
        self.paused = True 
        self.draw_window()  # Re draw screen to update pause button
        while self.paused:  # wait until game is unpaused or quit
            for event in pygame.event.get(): 
                if event.type == pygame.QUIT:
                    self.running = False
                    self.paused = False
                    break
                elif event.type == pygame.KEYDOWN: 
                    if event.key == pygame.K_p: 
                        self.paused = False 
                        break
                    elif event.key == pygame.K_q:
                        self.running = False
                        self.paused = False
                        break
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    if 510<=x and x<560 and y<50:
                        self.paused = False
                        break

    def addTower(self, X, Y, type):
        """
        Append a new tower onto Towers
        type = 1 is purple, 2 is Orange, 3 is Green
        """
        if type == 1:
            temp = PurpleTower(X,Y)
        elif type == 2:
            temp = OrangeTower(X,Y)
        elif type == 3:
            temp = GreenTower(X,Y)
        self.towers.append(temp)
        self.money -= temp.cost

    def newWave(self):
        if self.enemies == []:
            self.money += self.wave*100
            self.wave += 1
            self.set_wave_enemies()
            if self.wave %10 == 0:
                self.incoming_boss_message()

    def set_wave_enemies(self):
        x = self.wave
        # Boss wave every 10 waves
        if x % 10 == 0:
            temp = Boss()
            temp.x = -100
            self.enemies.append(temp)
        else:
            for i in range(1,x*x+1):
                temp = Boss()
                temp.x = -50*i
                self.enemies.append(temp)

    def enemy_reached_end(self):
        for en in self.enemies:
            if en.x == 250 and en.y == 0:
                self.lives -= 1
                self.enemies.remove(en)

    def enemy_dead(self):
        for en in self.enemies:
            if en.health < 1:
                self.money += en.value
                self.enemies.remove(en)

    def draw(self, surface):
        # Displays things on the surface
        # Path
        self.path.draw(surface)
        # Enemies
        for en in self.enemies:
            if en.x > -50:
                en.draw(surface)

        # Towers
        for tower in self.towers:
            tower.draw(surface)

        # Lives, Money and Wave
        self.display_lives_waves_and_money(surface)

        # Music and Pause buttons
        self.display_music_and_pause_buttons(surface)

    def display_lives_waves_and_money(self,surface):
        font = pygame.font.Font('freesansbold.ttf', 32)
        heart = pygame.image.load('heart.png')
        surface.blit(heart,(700,0))
        dollar = pygame.image.load('dollar.png')
        surface.blit(dollar,(570,0))
        money = font.render(str(g.money), True, (0, 0, 0))
        surface.blit(money, (605,12))
        lives = font.render(str(g.lives), True, (0,0,0))
        surface.blit(lives,(755,12))
        # Colour of wave tells the player what tower is currently selected
        if self.selected_tower == 1:
            COLOUR = (160,32,240)   #Purple
        elif self.selected_tower == 2:
            COLOUR = (255, 165, 0)  #Orange
        elif self.selected_tower == 3:
            COLOUR = (0, 255, 0)    #Green

        wave = font.render('Wave ' + str(g.wave), True, COLOUR)
        surface.blit(wave,(320,12))

    def display_music_and_pause_buttons(self, surface):
        # Pause and Play button
        pause_button = pygame.image.load('pause.png')
        play_button = pygame.image.load('play.png')
        if self.paused == True:
            surface.blit(play_button, (510,0))
        else:
            surface.blit(pause_button, (510,0))

        # Music on and off buttons
        music_off = pygame.image.load('music_off.png')
        music_on = pygame.image.load('music_on.png')
        if self.music == True:
            surface.blit(music_on,(450,0))
        else:
            surface.blit(music_off,(450,0))

    def get_enemy_positions(self):
        positions = []
        for en in self.enemies:
            # If on screen append to list
            if en.x >= 0 and en.x < width and en.y >= 0 and en.y <= height:
                positions.append((en.x,en.y))

        return positions

    def get_tower_positions(self):
        positions = []
        for tower in self.towers:
            positions.append((tower.x,tower.y))

        return positions
     
def distance_tower_to_enemy(tower,enemy):
    tower_position = tower.x, tower.y
    enemy_position = enemy.x, enemy.y
    dif_x = tower.x - enemy.x
    dif_y = tower.y - enemy.y
    return math.sqrt(dif_x**2+ dif_y**2)

def main():
    global g
    g = Game()
    
    # Game loop
    while g.running:
        pygame.time.delay(30)
        
        # Mouse clicks and keyboard presses
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                g.running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                xx, yy = pygame.mouse.get_pos()
                
                # If click was made on path
                if g.path.click_on_path(xx, yy):
                    continue

                # Music button clicked
                elif 449<xx and xx<500 and yy<50:
                    g.music = not g.music
                    if g.music == False:
                        mixer.music.pause()
                    else:
                        mixer.music.unpause()

                # Pause button clicked
                elif 510<=xx and xx<560 and yy<50:
                    g.pause_game()

                # Restrict towers from being placed in top right
                elif xx > 324 and yy < 50:
                    continue
                    
                else:
                    # Check if we clicked on a tower or not
                    positions = g.get_tower_positions()
                    if ((xx//25)*25, (yy//25)*25) in positions:
                        xx = (xx//25)*25 
                        yy = (yy//25)*25
                        # If we have enough money upgrade tower
                        for tower in g.towers:
                            if g.money >= tower.upgradeCost and tower.x == xx and tower.y == yy and tower.level<9:
                                g.money -= tower.upgradeCost
                                tower.upgrade()
                    else:
                        # If we have enough money place a tower
                        if g.money >= 500:
                            g.addTower(xx,yy,g.selected_tower)

            # Pause music and game by mouse clicks
            if event.type == pygame.KEYDOWN:
                # Set selected tower using 1,2,3 keys
                if event.key == pygame.K_1:
                    g.selected_tower = 1
                elif event.key == pygame.K_2:
                    g.selected_tower = 2
                elif event.key == pygame.K_3:
                    g.selected_tower = 3

                # Press p to pause or unpause
                elif event.key == pygame.K_p:
                    g.pause_game()

                # Press m to pause or play music
                elif event.key == pygame.K_m:
                    g.music = not g.music
                    if g.music == False:
                        mixer.music.pause()
                    else:
                        mixer.music.unpause()

        # Move enemies
        for en in g.enemies:
            en.move(g.path)
        
        # Shoot enemy furthest down the path and at most 25 pixels off the screen
        for tower in g.towers:
            # Purple towers damage all enemies in range
            if tower.name == 'Purple' and tower.reload_time == 0 and en.x>-25:
                for en in g.enemies:
                    if tower.range >= distance_tower_to_enemy(tower,en):
                        en.health -= tower.damage
                        tower.reload_time = tower.max_reload_time
                        en.poisoned = True
                        en.poisoned_time = tower.max_poison_time
            # Non purple tower ready to shoot first enemy only
            elif tower.reload_time == 0:
                for en in g.enemies:
                    if tower.range >= distance_tower_to_enemy(tower,en) and en.x>-25:
                        en.health -= tower.damage
                        tower.reload_time = tower.max_reload_time
                        break
                
                    
        # Reduce reload time for towers by 1
        for tower in g.towers:
            if tower.reload_time > 0:
                tower.reload_time -=1

        # Apply poison effect to enemies and reduce effect length
        for en in g.enemies:
            if en.poisoned:
                en.health -= 2
                en.poisoned_time -=1
                if en.poisoned_time == 0:
                    en.poisoned = False


        # Check if any enemies have died
        g.enemy_dead()

        # Check if any enemies have reached the end
        g.enemy_reached_end()

        # Check for new wave
        g.newWave()

        # Game over
        if g.lives < 1:
            g.game_over_message()

        # Update screen
        g.draw_window()
        
main()