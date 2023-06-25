import pygame
from pygame import gfxdraw

from  numpy import sqrt, ndarray



class Button():
    def __init__(self, screen, x, y, width, height, buttonText='Button', font = None,onclickFunction=None, onePress=False, visible = True):
        self.x, self.y = x, y
        self.offsetx , self.offsety = 0 , 0
        
        self.width, self.height = width, height
        
        self.onclickFunction = onclickFunction

        self.onePress = onePress
        self.alreadyPressed = False
        self.time_down = 0

        self.fillColors = {
            'normal': '#ffffff',
            'hover': '#666666',
            'pressed': '#333333',
        }


        self.text = buttonText
        self.font = font

        self.screen = screen

        if visible: self.make_surface()


    def make_surface(self):
        self.buttonSurface = pygame.Surface((self.width, self.height))
        self.buttonRect = pygame.Rect(self.x, self.y, self.width, self.height)

        if self.font: self.buttonSurf = self.font.render(self.text, True, (20, 20, 20))

        self.alreadyPressed = False
    def process(self):

        mousePos = pygame.mouse.get_pos()
        
        self.buttonSurface.fill(self.fillColors['normal'])
        if self.buttonRect.collidepoint(mousePos):
            self.buttonSurface.fill(self.fillColors['hover'])

            if pygame.mouse.get_pressed(num_buttons=3)[2]:
                self.buttonSurface.fill(self.fillColors['pressed'])

                if self.onePress:
                    self.onclickFunction(self)

                elif not self.alreadyPressed:
                    self.onclickFunction(self)
                    self.alreadyPressed = True

            else:
                self.alreadyPressed = False

        self.buttonSurface.blit(self.buttonSurf, [
            self.buttonRect.width/2 - self.buttonSurf.get_rect().width/2,
            self.buttonRect.height/2 - self.buttonSurf.get_rect().height/2
        ])
        self.screen.blit(self.buttonSurface, self.buttonRect)

class ContextMenu(Button):
    
    def __init__(self, screen, x, y, buttonlist, onePress=False):

        self.offsetx, self.offsety = 0, 100

        self.buttons = buttonlist

        width = max(button.width for button in self.buttons)
        height = sum(button.height for button in self.buttons)

        Button.__init__(self,  screen, x, y, width, height, visible=False )
        

    def make_surface(self):
        self.x ,self.y = pygame.mouse.get_pos()
        self.x += self.offsetx
        self.y += self.offsety
        step = 0
        for button in self.buttons:
            button.x  = self.x
            button.y = self.y + step
            step+=button.height
            button.make_surface()

        Button.make_surface(self)

    def check_time_elapsed(self, timespan = 10):
        time_elapsed = pygame.time.get_ticks() - self.time_down
        return time_elapsed > timespan

    def process(self):
        
        mousePos = pygame.mouse.get_pos()
        
        if not(self.alreadyPressed) and pygame.mouse.get_pressed(num_buttons=3)[2]:
            if self.check_time_elapsed(): 
                self.time_down = pygame.time.get_ticks()
                self.make_surface()
                self.alreadyPressed = True

        if self.alreadyPressed:
            for button in self.buttons:
                button.process()
            if not(self.buttonRect.collidepoint(mousePos)) and pygame.mouse.get_pressed(num_buttons=3)[0]:
                if self.check_time_elapsed(): 
                    self.time_down = pygame.time.get_ticks()
                    self.alreadyPressed = False

        
class MenuButton(Button):
    def __init__(self, screen, x, y, width, height, buttonText='>', font = None,menu=None, onePress=False):
        self.menu = menu
        super().__init__(screen, x, y, width, height, buttonText,font, self.menu.process, onePress)
    def process(self):
        mousePos = pygame.mouse.get_pos()
        self.buttonSurface.fill(self.fillColors['normal'])
        if self.buttonRect.collidepoint(mousePos):
            self.buttonSurface.fill(self.fillColors['hover'])

            if pygame.mouse.get_pressed(num_buttons=3)[2]:
                self.alreadyPressed = True
                self.buttonSurface.fill(self.fillColors['pressed'])

            elif pygame.mouse.get_pressed(num_buttons=3)[0]:
                self.alreadyPressed = False
        if self.alreadyPressed:
            self.menu.offsetx = -mousePos[0] + self.x + self.width
            self.menu.offsety =  -mousePos[1] + self.y 
            self.onclickFunction(self)

        self.buttonSurface.blit(self.buttonSurf, [
            self.buttonRect.width/2 - self.buttonSurf.get_rect().width/2,
            self.buttonRect.height/2 - self.buttonSurf.get_rect().height/2
        ])
        self.screen.blit(self.buttonSurface, self.buttonRect)

class Window:
    def __init__(self, sim, config={}):
        pygame.init()

        # Simulation to draw
        self.sim = sim

        # Set default configurations
        self.set_default_config()

        # Update configurations
        for attr, val in config.items():
            setattr(self, attr, val)

    def set_disable_menu(self): 
        self.disable_menu_loop = not(self.disable_menu_loop)
     
    def set_default_config(self):
        """Set default configuration"""
        self.width,self.height  = 1920,1080

        
        # Create a pygame window
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.flip()

        self.bg_color = (0,0,0)
        self.road_color = (240,248,255)
        self.car_color = (0,0,205)
        self.build_color = (205,0,205)
        

        self.time_stop = 10000

        self.fps = 30
        # To draw text
        pygame.font.init()
        self.text_font = pygame.font.SysFont('Lucida Console', 12)


        self.zoom = 1
        self.offset = (0, 0)

        self.mouse_last = (0, 0)
        self.mouse_down = False

        self.pmes = f''


        
        self.objects = []


        def faster(button = None):
            self.steps_per_update*=10
            self.steps_per_update+=1
        def slower(button = None):
            self.steps_per_update= int( self.steps_per_update*0.1)

        def pause(button = None):
            self.steps_per_update = not(self.steps_per_update)

        def get_nodes(button = None):
            roads_id_list = self.find_object_osmid_on_pos(pos = pygame.mouse.get_pos(), objects = self.sim.roads.values())
            button_text = "NODES "
            text_size = 12
            sep = "   "
            if not(isinstance(button, Button)): return
            
            button.text = button_text + sep.join([  self.sim.roads[osmid].nodes for osmid in roads_id_list ])
            button.width = 30+ text_size*len(button.text)
            button.make_surface()
            
        def get_edges(button = None):
            roads_id_list = self.find_object_osmid_on_pos(pos = pygame.mouse.get_pos(), objects = self.sim.roads.values())
            button_text = "EDGES "
            text_size = 12
            sep = "   "
            if not(isinstance(button, Button)): return
            
            button.text = button_text + sep.join([  str(osmid) for osmid in roads_id_list ])
            button.width = 30+ text_size*len(button.text)
            button.make_surface()
        
        width = height = 20

        self.objects += [
            Button(self.screen, self.width - width,   self.height - height, width, height, '\u00BB', self.text_font, onclickFunction = faster, visible=True),
            Button(self.screen, self.width - 2*width, self.height - height, width, height, '\u00AB', self.text_font, onclickFunction = slower, visible=True),
            Button(self.screen, self.width - 3*width, self.height - height, width, height, '||',     self.text_font, onclickFunction = pause,  visible=True)
       
        ]
        
        customMenu = ContextMenu( self.screen, 0,0, [
            Button(self.screen,0, 0, height, width, self.pmes, self.text_font, onclickFunction = get_nodes,onePress=True,  visible=False),
            Button(self.screen,0, 0, height, width, self.pmes, self.text_font, onclickFunction = get_edges,onePress=True,  visible=False),
        ])
        self.objects.append(customMenu)
        #self.customButton = MenuButton(self.screen,0, 0, 10, 10, '>', self.text_font, customMenu, False)


        

    def loop(self, loop=None):
        """Shows a window visualizing the simulation and runs the loop function."""
        
        # Fixed fps
        clock = pygame.time.Clock()
       

       

        # Draw loop
        running = True
        while running:
            # Update simulation
            if loop: loop(self.sim)
            if self.sim.t>self.time_stop: 
                running = False
            # Draw simulation
            self.draw()


            # Handle all button events
            for object in self.objects:
                object.process()


            # Update window
            pygame.display.update()
            clock.tick(self.fps)

            # Handle all events
            for event in pygame.event.get():
                # Quit program if window is closed
                if event.type == pygame.QUIT:
                    running = False
                # Handle mouse events
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # If mouse button down
                    if event.button == 1:
                        # Left click
                        x, y = pygame.mouse.get_pos()
                        x0, y0 = self.offset
                        self.mouse_last = (x-x0*self.zoom, y-y0*self.zoom)
                        self.mouse_down = True
                    if event.button == 4:
                        # Mouse wheel up
                        self.pmes = ' '
                        self.zoom *=  (self.zoom**2+self.zoom/4+1) / (self.zoom**2+1)
                    if event.button == 5:
                        # Mouse wheel down 
                        self.pmes = ' '
                        self.zoom *= (self.zoom**2+1) / (self.zoom**2+self.zoom/4+1)
                    if event.button == 3:
                        # Right click 
                        self.mouse_down = False
                        self.mouse_last = pygame.mouse.get_pos()
                        self.pmes = self.find_object_on_pos(self.mouse_last,self.sim.roads.values())
                elif event.type == pygame.MOUSEMOTION:
                    # Drag content
                    if self.mouse_down:
                        self.pmes = ' '
                        x1, y1 = self.mouse_last
                        x2, y2 = pygame.mouse.get_pos()
                        self.offset = ((x2-x1)/self.zoom, (y2-y1)/self.zoom)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.mouse_down = False    
        #pygame.quit()
    
    def run(self, steps_per_update=1):
        """Runs the simulation by updating in every loop."""
        self.steps_per_update = steps_per_update
        def loop(sim):
            sim.run(self.steps_per_update)
        self.loop(loop)

    def convert(self, x, y=None):
        """Converts simulation coordinates to screen coordinates"""
        if isinstance(x, list):
            return [self.convert(e[0], e[1]) for e in x]
        if isinstance(x, tuple):
            return self.convert(*x)
        if isinstance(x, ndarray):
            return self.convert(*x)    

        x, y = int(self.width/2 + (x + self.offset[0])*self.zoom), int(self.height/2 + (y + self.offset[1])*self.zoom)
        return x, y

    def inverse_convert(self, x, y=None):
        """Converts screen coordinates to simulation coordinates"""
        if isinstance(x, list):
            return [self.inverse_convert(e[0], e[1]) for e in x]
        if isinstance(x, tuple):
            return self.inverse_convert(*x)
        return (
            int(-self.offset[0] + (x - self.width/2)/self.zoom),
            int(-self.offset[1] + (y - self.height/2)/self.zoom)
        )
    def find_object_osmid_on_pos(self, pos, objects):
        x,y =  self.inverse_convert(pos)
        osmid = []
        for obj in objects:
            x1,y1 = obj.start
            x2,y2 = obj.end
            if x1<=x<=x2 or  x1>=x>=x2:
                delta1 = ((x-x2)) ** 2 + ((y-y2)) ** 2
                if delta1 < 100:
                    osmid.append(obj.osmid)
        return osmid
    def find_object_on_pos(self, pos, objects):
        inx_c_pos = self.inverse_convert(pos)
        pmes = f"{inx_c_pos}"
        osmid_list = self.find_object_osmid_on_pos(pos, objects)
        for osmid in osmid_list:
            pmes += f'|{osmid}'
        return pmes
    def background(self, r, g, b):
        """Fills screen with one color."""
        self.screen.fill((r, g, b))

    def line(self, start_pos, end_pos, color):
        """Draws a line."""
        gfxdraw.line(
            self.screen,
            *start_pos,
            *end_pos,
            color
        )

    def rect(self, pos, size, color):
        """Draws a rectangle."""
        gfxdraw.rectangle(self.screen, (*pos, *size), color)

    def box(self, pos, size, color):
        """Draws a rectangle."""
        gfxdraw.box(self.screen, (*pos, *size), color)

    def circle(self, pos, radius, color, filled=True):
        gfxdraw.aacircle(self.screen, *pos, radius, color)
        if filled:
            gfxdraw.filled_circle(self.screen, *pos, radius, color)



    def polygon(self, vertices, color, filled=True):
        gfxdraw.aapolygon(self.screen, vertices, color)
        if filled:
            gfxdraw.filled_polygon(self.screen, vertices, color)

    def rotated_box(self, pos, size, angle=None, cos=None, sin=None, centered=True, color=(155, 89, 182), filled=True):
        """Draws a rectangle center at *pos* with size *size* rotated anti-clockwise by *angle*."""
        x, y = pos
        l, h = size

        if angle:
            cos, sin = cos(angle), np.sin(angle)
        
        vertex = lambda e1, e2: (
            x + (e1*l*cos + e2*h*sin)/2,
            y + (e1*l*sin - e2*h*cos)/2
        )

        if centered:
            vertices = self.convert(
                [vertex(*e) for e in [(-1,-1), (-1, 1), (1,1), (1,-1)]]
            )
        else:
            vertices = self.convert(
                [vertex(*e) for e in [(0,-1), (0, 1), (2,1), (2,-1)]]
            )

        self.polygon(vertices, color, filled=filled)

    def rotated_rect(self, pos, size, angle=None, cos=None, sin=None, centered=True, color=(0, 0, 255)):
        self.rotated_box(pos, size, angle=angle, cos=cos, sin=sin, centered=centered, color=color, filled=False)

    def arrow(self, pos, size, angle=None, cos=None, sin=None, color=(150, 150, 190)):
        if angle:
            cos, sin = cos(angle), np.sin(angle)
        
        self.rotated_box(
            pos,
            size,
            cos=(cos - sin) / sqrt(2),
            sin=(cos + sin) / sqrt(2),
            color=color,
            centered=False
        )

        self.rotated_box(
            pos,
            size,
            cos=(cos + sin) / sqrt(2),
            sin=(sin - cos) / sqrt(2),
            color=color,
            centered=False
        )


    def draw_axes(self, color=(147,112,219)):
        x_start, y_start = self.inverse_convert(0, 0)
        x_end, y_end = self.inverse_convert(self.width, self.height)
        self.line(
            self.convert((0, y_start)),
            self.convert((0, y_end)),
            color
        )
        self.line(
            self.convert((x_start, 0)),
            self.convert((x_end, 0)),
            color
        )

    def draw_grid(self, unit=50, color=(255,0,255)):
        x_start, y_start = self.inverse_convert(0, 0)
        x_end, y_end = self.inverse_convert(self.width, self.height)

        n_x = int(x_start / unit)
        n_y = int(y_start / unit)
        m_x = int(x_end / unit)+1
        m_y = int(y_end / unit)+1

        for i in range(n_x, m_x):
            self.line(
                self.convert((unit*i, y_start)),
                self.convert((unit*i, y_end)),
                color
            )
        for i in range(n_y, m_y):
            self.line(
                self.convert((x_start, unit*i)),
                self.convert((x_end, unit*i)),
                color
            )

    # def draw_arrows(self, lane_start, length, cos, sin, n = 10, dir = 1):
    #     for i in np.arange(-0.4*length, 0.4*length, n):
    #         pos = (
    #             lane_start[0] + (length/2 + i) * cos,
    #             lane_start[1] + (length/2 + i) * sin
    #         )
    #         self.arrow(
    #             pos,
    #             (-1.25*dir, 0.2),
    #             cos=cos,
    #             sin=sin
    #         )  
    def draw_buildings(self):
        color = self.build_color
        
        buildings = self.sim.buildings
        for poly in buildings:
            vert = list(map(self.convert, poly))
            self.polygon(color = color,vertices= vert)

    def draw_road_number(self,road):
        
        text_road_no = self.text_font.render(f'№{road.osmid}', False, (255, 201, 0))
        x, y  = road.end
        y+=10
        road_coord = self.convert(x, y)
        self.screen.blit(text_road_no, road_coord)

    def draw_roads(self):
        color = self.road_color
        for road in self.sim.roads.values():
            #self.draw_road_number(road)
            

            for lane in road.lanes_forward:
                # Draw road background
                self.rotated_box(
                    lane.start,
                    (road.length, road.lane_width),
                    cos=road.angle_cos,
                    sin=road.angle_sin,
                    color=color,
                    centered=False
                )
                
            # for lane in road.lanes_backward:
            #     # Draw road background
            #     self.rotated_box(
            #         lane.end,
            #         (road.length, road.lane_width),
            #         cos=road.angle_cos,
            #         sin=road.angle_sin,
            #         color=color,
            #         centered=False
            #     )
            
            # Draw road arrow
            # if road.length > 5: self.draw_arrows(lane.end, road.length, road.angle_cos, road.angle_sin, 10, -1)


    def draw_vehicle(self, vehicle, sin,cos, lane):
        l, h = vehicle.l,  2

        color = self.car_color
        
        x = lane.start[0] + cos * vehicle.x 
        y = lane.start[1] + sin * vehicle.x 

        self.rotated_box((x, y), (l, h), cos=cos, sin=sin, centered=True, color=color)

    def draw_vehicles(self):
        for road in self.sim.roads.values():
            for lane in road.lanes_forward:
                # Draw vehicles
                for vehicle in lane.vehicles:
                    sin, cos = road.angle_sin, road.angle_cos
                    self.draw_vehicle(vehicle, sin, cos, lane)

    def draw_signals(self):
        for signal in self.sim.traffic_signals:
            for i in range(len(signal.phase_order)):
                color = (0, 255, 0) if signal.current_cycle[i] else (255, 0, 0)
                for lane in signal.phase_order[i]:
                    a = 1
                    position = (
                        (1-a)*lane.start[0] + a*lane.end[0],        
                        (1-a)*lane.start[1] + a*lane.end[1]
                    )
                    self.rotated_box(
                        position,
                        (2, 2),
                        cos=0, sin=1,
                        color=color)

    def draw_status(self):
        text_fps = self.text_font.render(f't={self.sim.t:.5}', False, self.road_color)
        text_frc = self.text_font.render(f'n={self.sim.frame_count}', False, self.road_color)
        text_road_no = self.text_font.render(self.pmes, False, self.car_color)   
                        

        self.screen.blit(text_fps, (0, 0))
        self.screen.blit(text_frc, (100, 0))
        self.screen.blit(text_road_no, self.mouse_last )


    def draw(self):
        # Fill background
        self.background(*self.bg_color)

        # Major and minor grid and axes
        # self.draw_grid(10, (220,220,220))
        self.draw_grid(100, (200,200,200))
        self.draw_grid(500)

        # self.draw_axes()


        self.draw_buildings()
        self.draw_roads()
        self.draw_vehicles()
        self.draw_signals()
        

        # Draw status info
        self.draw_status()
        