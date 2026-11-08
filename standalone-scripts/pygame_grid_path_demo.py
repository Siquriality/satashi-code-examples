# Рисует сетку Pygame, препятствия и движение к цели.
import time
import pygame
import sys
import random

pygame.init()

def draw_grid(screen, grid_size, color):
    for x in range(0, screen.get_width(), grid_size):
        pygame.draw.line(screen, color, (x, 0), (x, screen.get_height()))
    for y in range(0, screen.get_height(), grid_size):
        pygame.draw.line(screen, color, (0, y), (screen.get_width(), y))

def main():
    w, h = 800, 600
    grid_size = 20
    screen = pygame.display.set_mode((w, h))
    pygame.display.set_caption("Animation")
    clock = pygame.time.Clock()

    player_pos = [0, 0]
    goal_pos = [w // grid_size - 1, h // grid_size - 1]
    obstacles = []

    running = True
    while running:
        screen.fill((0, 0, 0))
        draw_grid(screen, grid_size, (40, 40, 40))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                ox, oy = mx // grid_size, my // grid_size
                if [ox, oy] not in obstacles and [ox, oy] != player_pos and [ox, oy] != goal_pos:
                    obstacles.append([ox, oy])

        for obs in obstacles:
            pygame.draw.rect(screen, (255, 0, 0), (obs[0] * grid_size, obs[1] * grid_size, grid_size, grid_size))

        pygame.draw.rect(screen, (0, 255, 0), (player_pos[0] * grid_size, player_pos[1] * grid_size, grid_size, grid_size))
        pygame.draw.rect(screen, (0, 0, 255), (goal_pos[0] * grid_size, goal_pos[1] * grid_size, grid_size, grid_size))

        if player_pos != goal_pos:
            dx = goal_pos[0] - player_pos[0]
            dy = goal_pos[1] - player_pos[1]
            if abs(dx) > abs(dy):
                step = [1 if dx > 0 else -1, 0]
            else:
                step = [0, 1 if dy > 0 else -1]
            next_pos = [player_pos[0] + step[0], player_pos[1] + step[1]]
            if next_pos not in obstacles:
                player_pos = next_pos

        pygame.display.flip()
        clock.tick(10)

    pygame.quit()
    sys.exit()

main()
 if args.info:
        print("System Information:")
        print(f"Platform: {sys.platform}")
        print(f"Python Version: {sys.version}")

    if args.create:
        print(f"Creating file: {args.create}")
        try:
            with open(args.create, 'w') as f:
                f.write("")
            print(f"File '{args.create}' created successfully.")
        except Exception as e:
            print(f"Error creating file: {e}")

    if args.delete:
        print(f"Deleting file: {args.delete}")
        try:
            os.remove(args.delete)
            print(f"File '{args.delete}' deleted successfully.")
        except FileNotFoundError:
            print(f"File '{args.delete}' not found.")
        except Exception as e:
            print(f"Error deleting file: {e}")