import pybullet as p
import time
import numpy as np
import pybullet_data
import random
import cv2
import matplotlib as plt
from string import ascii_uppercase

# ANSI escape codes for some colors
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
ENDC = '\033[0m'  # Reset color

# Print colored text
print(f"{RED}Red Text{ENDC}")
print(f"{GREEN}Green Text{ENDC}")
print(f"{YELLOW}Yellow Text{ENDC}")

# Start PyBullet in GUI mode
p.connect(p.GUI)

# Set gravity
p.setGravity(0, 0, 0)


# Set fog color to black

p.configureDebugVisualizer(p.COV_ENABLE_DEPTH_BUFFER_PREVIEW,0)
p.configureDebugVisualizer(p.COV_ENABLE_SEGMENTATION_MARK_PREVIEW,0)
p.setPhysicsEngineParameter(fixedTimeStep=1. / 240., numSolverIterations=5, numSubSteps=2)
p.setPhysicsEngineParameter(enableConeFriction=0)
p.setPhysicsEngineParameter(enableFileCaching=0)
p.configureDebugVisualizer(p.COV_ENABLE_SHADOWS,0)

# Add PyBullet's data directory to its search path
p.setAdditionalSearchPath(pybullet_data.getDataPath())

# Load a plane and change its color to black
planeId = p.loadURDF("plane.urdf", basePosition=[0,0,-0.65], useMaximalCoordinates=True)
p.changeVisualShape(planeId, -1, rgbaColor=[0, 0, 0, 1])

# CubeSat dimensions in meters (3U CubeSat)
cube_length = 0.1  # 10cm
cube_width = 0.1  # 10cm
cube_height = 0.3  # 30cm

# Mass of the CubeSat in kilograms
mass = 1

# Collision and visual shape
collisionShapeId = p.createCollisionShape(shapeType=p.GEOM_BOX,
                                          halfExtents=[cube_length / 2, cube_width / 2, cube_height / 2])
visualShapeId = p.createVisualShape(shapeType=p.GEOM_BOX,
                                    halfExtents=[cube_length / 2, cube_width / 2, cube_height / 2],
                                    rgbaColor=[1, 0, 0, 1])  # Red color

# Create the CubeSat body
cubeSatId = p.createMultiBody(baseMass=mass,
                              baseCollisionShapeIndex=collisionShapeId,
                              baseVisualShapeIndex=visualShapeId,
                              basePosition=[0, 0, 0.5])

# Camera parameters
camera_distance = 0.5  # Adjust based on desired distance from the CubeSat side
aspect = 1
near = 0.01
far = 4
fov = 50


# Grid parameters
grid_size = 5  # 5x5 grid
object_spacing = 0.15  # Spacing between objects in the grid
initial_position = np.array([1, -0.3, 0.1])  # Initial position of the first object in the grid
objects = []

# Create a 5x5 grid of objects
for i in range(grid_size):
    for j in range(grid_size):
        pos = initial_position + np.array([0, object_spacing * i, object_spacing * j])
        visual_shape_id = p.createVisualShape(shapeType=p.GEOM_SPHERE,
                                              #halfExtents=[0.05, 0.05, 0.05],
                                              radius = 0.05,
                                              rgbaColor=[0, 0, 0, 0])
        collision_shape_id = p.createCollisionShape(shapeType=p.GEOM_BOX,
                                                    halfExtents=[0.05, 0.05, 0.05])
        obj_id = p.createMultiBody(baseMass=0,
                                   baseCollisionShapeIndex=collision_shape_id,
                                   baseVisualShapeIndex=visual_shape_id,
                                   basePosition=pos)
        objects.append(obj_id)


def place_heat_sources_random(temp_grid, n):
    for _ in range(n):
        x, y = random.randint(0, 4), random.randint(0, 4)
        temp_grid[x][y] = random.randint(25, 100)

def initialize_grid_with_white_corners(objects,temp_grid):

    new_temp_grid = np.copy(temp_grid)  # Create a copy to update temperatures


    new_temp_grid[0][0] = 100
    new_temp_grid[0][4] = 100
    new_temp_grid[4][4] = 100
    new_temp_grid[4][0] = 100
    for i in range(5):
        for j in range(5):
            obj_id = objects[i * 5 + j]
            temp = new_temp_grid[i, j]
            # Map temperature to grayscale value (25-100 mapped to 0-255)
            grayscale_value = np.interp(temp, [25, 100], [0, 255])
            normalized_value = grayscale_value / 255.0
            color = [normalized_value] * 3 + [1]  # Grayscale, alpha set to 1
            p.changeVisualShape(obj_id, -1, rgbaColor=color)

    wait_for_key_press()
def update_fire(grid,temp_grid):
    new_temp_grid = np.copy(temp_grid)  # Create a copy to update temperatures

    for i in range(5):
        for j in range(5):
            if grid[i][j] != 'fire':
                # Randomly adjust temperatures
                new_temp_grid[i][j] = max(25, new_temp_grid[i][j] + random.randint(-2, 2))

            # Fire cells logic
            if grid[i][j] == 'fire':
                # Fire might spread or go out
                if random.random() < 0.7:  # 70% chance to cool down
                    new_temp_grid[i][j] = random.randint(25, 49)
                else:  # Heat up adjacent squares
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            ni, nj = i + dx, j + dy
                            if 0 <= ni < 5 and 0 <= nj < 5:
                                new_temp_grid[ni][nj] = min(new_temp_grid[ni][nj] + random.randint(5, 15), 100)

    return new_temp_grid

# Initialize a temperature grid
temp_grid = np.full((5, 5), 25)  # Start with all cells at a base temperature of 25

# Place initial heat sources
# place_heat_sources_random(temp_grid, 5)

# Wall parameters
wall_length = 2.0  # Length of each wall
wall_height = 2  # Height of the walls
wall_thickness = 0.05  # Thickness of the walls

# Wall positions and orientations
wall_positions = [
    [0, wall_length / 2, wall_height / 2],  # North wall
    [0, -wall_length / 2, wall_height / 2],  # South wall
    [wall_length / 2, 0, wall_height / 2],  # East wall
    [-wall_length / 2, 0, wall_height / 2],  # West wall
]
wall_orientations = [
    [0, 0, 0, 1],  # North wall
    [0, 0, 0, 1],  # South wall
    [0, 0, 0.70710678118, 0.70710678118],  # East wall (90 degrees rotation)
    [0, 0, 0.70710678118, 0.70710678118],  # West wall (90 degrees rotation)
]

# Create the walls
for i in range(4):
    wall_id = p.createMultiBody(
        baseMass=0,
        baseCollisionShapeIndex=p.createCollisionShape(p.GEOM_BOX, halfExtents=[wall_length / 2, wall_thickness / 2, wall_height / 2]),
        baseVisualShapeIndex=p.createVisualShape(p.GEOM_BOX, halfExtents=[wall_length / 2, wall_thickness / 2, wall_height / 2], rgbaColor=[0, 0, 0, 1]),
        basePosition=wall_positions[i],
        baseOrientation=wall_orientations[i]
    )


# Function to update colors based on temperature
def update_colors_based_on_temp(objects, temp_grid):

    for i in range(5):
        for j in range(5):
            obj_id = objects[i * 5 + j]
            temp = temp_grid[i, j]

            # Map temperature to grayscale value (25-100 mapped to 0-255)
            #grayscale_value = np.interp(temp, [25, 100], [100, 25])
            normalized_value = temp / 255.0

            color = [normalized_value] * 3 + [1]  # Grayscale, alpha set to 1
            p.changeVisualShape(obj_id, -1, rgbaColor=color)




def wait_for_key_press(key='p'):
    print("Press 'p' to continue...")
    key_pressed = False
    while not key_pressed:
        keys = p.getKeyboardEvents()
        # Check if 'p' key is pressed
        # 'p' key has a keycode of 112
        if ord(key) in keys and keys[ord(key)] & p.KEY_WAS_TRIGGERED:
            key_pressed = True
        p.stepSimulation()


def get_centroid(contour):
    # Function to calculate centroid of a contour
    moment = cv2.moments(contour)
    cx = int(moment['m10'] / moment['m00'])
    cy = int(moment['m01'] / moment['m00'])
    return (cx, cy)


def interpolate(start, end, num_points):
    # Function to interpolate points between two centroids
    return np.round(np.linspace(start, end, num=num_points)).astype(int)

def find_grid(image):
    # First, let's find the edges in the image
    edges = cv2.Canny(image, 100, 150, apertureSize=3)

    # Find contours in the edged image, keep only the largest ones
    contours, _ = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:4]  # Keep the four largest contours

    # Calculate centroids for each contour
    centroids = [get_centroid(contour) for contour in contours]

    # Convert centroids list to a NumPy array for advanced indexing
    centroids = np.array(centroids)

    # Step 1: Sort by y coordinate
    centroids_sorted_by_y = centroids[np.argsort(centroids[:, 1])]

    # Step 2: Split into top and bottom halves, then sort those by x
    top_half = centroids_sorted_by_y[:2]
    bottom_half = centroids_sorted_by_y[2:]

    top_sorted_by_x = top_half[np.argsort(top_half[:, 0])]
    bottom_sorted_by_x = bottom_half[np.argsort(bottom_half[:, 0])]

    # Combine back
    sorted_centroids = np.vstack([top_sorted_by_x, bottom_sorted_by_x])
    top_left, top_right, bottom_left, bottom_right = sorted_centroids

    # centroids = np.array(sorted(centroids, key=lambda x: x[0] + x[1]))
    # top_left, top_right, bottom_right, bottom_left = centroids[0], centroids[1], centroids[3], centroids[2]

    # Number of points including the corners
    num_points = 5

    # Interpolate points along the edges of the square
    top_edge = interpolate(top_left, top_right, num_points)
    bottom_edge = interpolate(bottom_left, bottom_right, num_points)
    left_edge = interpolate(top_left, bottom_left, num_points)
    right_edge = interpolate(top_right, bottom_right, num_points)

    # Generate grid points
    grid_points = np.array([interpolate(left_edge[i], right_edge[i], num_points) for i in range(num_points)]).reshape(
        -1, 2)
    print(grid_points)
    return grid_points


def interpolate_grid_points(sorted_corners, grid_size):
    """
    Interpolate grid points for a 5x5 grid based on four sorted corner points.

    :param sorted_corners: A list of tuples representing the four corner points
                           [(top_left), (top_right), (bottom_left), (bottom_right)].
    :param grid_size: The size of the grid, assuming a square grid.
    :return: A list of tuples representing the interpolated grid points.
    """
    top_left, top_right, bottom_left, bottom_right = sorted_corners

    # Calculate horizontal and vertical steps
    horizontal_step = [(top_right[0] - top_left[0]) / (grid_size - 1),
                       (top_right[1] - top_left[1]) / (grid_size - 1)]
    vertical_step = [(bottom_left[0] - top_left[0]) / (grid_size - 1),
                     (bottom_left[1] - top_left[1]) / (grid_size - 1)]

    # Initialize list to hold grid points
    grid_points = []

    # Interpolate points
    for i in range(grid_size):
        for j in range(grid_size):
            # Calculate the interpolated point
            point_x = int(top_left[0] + j * horizontal_step[0] + i * vertical_step[0])
            point_y = int(top_left[1] + j * horizontal_step[1] + i * vertical_step[1])
            grid_points.append((point_x, point_y))

    return grid_points


def read_centroid_intensity(image, grid_points, area_size = 5, area_mode = False):
    """
    Reads the pixel intensity of all centroid areas on the image.

    :param image: The image to read from
    :param grid_points: The list of centroid points (x, y)
    :return: A list of pixel intensities
    """
    intensities = []
    # Assuming the centroid area is a single pixel for simplicity

    if area_mode == False:
        for x, y in grid_points:
            # Ensure the coordinates are within the image bounds
            if x >= 0 and y >= 0 and y < image.shape[0] and x < image.shape[1]:
                intensity = image[y, x]  # OpenCV images are accessed with y, x
                intensities.append(intensity)
            else:
                intensities.append(None)  # None for centroids outside the bounds

    # If the centroid covers more area, we would need to define the area size and average the intensities
    else:
        offset = area_size // 2  # Calculate offset from the centroid to the edges of the square

        for x, y in grid_points:
            # Define the square area around the centroid within the image bounds
            x_start = max(x - offset, 0)
            y_start = max(y - offset, 0)
            x_end = min(x + offset + 1, image.shape[1])
            y_end = min(y + offset + 1, image.shape[0])

            # Extract the area around the centroid
            centroid_area = image[y_start:y_end, x_start:x_end]

            # Calculate the average intensity if the area is not empty
            if centroid_area.size > 0:
                average_intensity = np.mean(centroid_area)
                intensities.append(average_intensity)
            else:
                intensities.append(None)  # None for centroids where no valid area could be defined

    return intensities


# Function to return color based on classification
def get_color(classification):
    if classification == 'fire':
        return RED
    elif classification == 'evac':
        return YELLOW
    elif classification == 'safe':
        return GREEN
    return ENDC

def classify_grid(intensities):
    """
    Scales the intensity values from 0-255 to 25-100 and classifies them based on brightness.
    Brightness classification:
    - 'fire' for brightness >= 50
    - 'evac' for brightness >= 25
    - 'safe' otherwise

    :param intensities: A list of intensity values
    :return: A list of classifications
    """
    intensities = np.array(intensities)
    #letters = list(ascii_uppercase)[:25]
    classifications = np.empty((5,5),dtype='U4')
    print(intensities)
    for i in range(5):

        for j in range(5):
            if intensities[i][j] >= 50:
                classifications[i][j] = 'fire'
            elif np.any(intensities[max(0, i-1):min(5, i+2), max(0, j-1):min(5, j+2)] >= 50):
                classifications[i][j] = 'evac'
            else:
                classifications[i][j] = 'safe'

    return classifications

integral_error = [0, 0, 0]
previous_error = [0, 0, 0]

def apply_orientation_correction(body_id, target_orientation):
    global integral_error, previous_error
    # Function to compute the difference in orientation and apply correction
    # PID controller parameters
    Kp = 1
    Ki = 0.005
    Kd = 0.3

    dt = 1. / 240.
    #dt = 2  # Simulation timestep

    # Get the current orientation
    _, current_orientation = p.getBasePositionAndOrientation(body_id)

    # Calculate the difference in orientation
    # This uses quaternion multiplication to get the relative rotation (difference)
    q_diff = p.getDifferenceQuaternion(current_orientation, target_orientation)

    # Convert quaternion difference to euler angles for simpler control logic
    diff_euler = p.getEulerFromQuaternion(q_diff)

    # Calculate integral and derivative of error
    integral_error = [ie + de * dt for ie, de in zip(integral_error, diff_euler)]
    derivative_error = [(de - pe) / dt for de, pe in zip(diff_euler, previous_error)]
    previous_error = diff_euler

    # PID control for torque
    torque = [Kp * e + Ki * ie + Kd * de for e, ie, de in zip(diff_euler, integral_error, derivative_error)]

    print(f"Target Orn:{target_orientation}\nCurrent Orn:{current_orientation}\nTorque Applied: {torque}\n")
    # Apply torque to correct orientation
    p.applyExternalTorque(body_id, -1, torque, p.WORLD_FRAME)

initialize_grid_with_white_corners(objects, temp_grid)
# Run the simulation
for i in range(1000):

    p.stepSimulation()


    # Get CubeSat state
    pos, ori = p.getBasePositionAndOrientation(cubeSatId)

    # Calculate camera position (on the side of the CubeSat)
    # Adjust the offset for the camera to be positioned on the side
    #camera_offset = [0, cube_width / 2 + camera_distance, cube_height / 4]  # Adjust the z value as needed
    camera_offset = [0, cube_width / 2, cube_height / 4]  # Adjust the z value as needed
    camera_pos = np.array(pos) + np.array(p.rotateVector(ori, camera_offset))

    # Camera target position: Looking straight out from the side
    camera_target_offset = [1, 0, 0]  # Adjust based on the orientation you desire for the camera
    camera_target_pos = np.array(pos) + np.array(p.rotateVector(ori, camera_target_offset))

    # Compute view matrix
    view_matrix = p.computeViewMatrix(cameraEyePosition=camera_pos,
                                      cameraTargetPosition=camera_target_pos,
                                      cameraUpVector=[0, 0, 1])  # Keep the up vector aligned with the world Z-axis

    # Compute projection matrix
    projection_matrix = p.computeProjectionMatrixFOV(fov, aspect, near, far)

    # Get camera image
    width, height, rgbImg, depthImg, segImg = p.getCameraImage(width=256, height=256,
                                                               viewMatrix=view_matrix,
                                                               projectionMatrix=projection_matrix)

    # Reshape and convert the flat rgbImg array to a (height, width, 4) image
    image_array = np.reshape(rgbImg, (height, width, 4))

    # Ensure the array is of type uint8
    image_array = np.array(image_array, dtype=np.uint8)

    # Convert to an RGB image by discarding the alpha channel
    image_rgb = image_array[:, :, :3]

    # Ensure the image is in the correct format for OpenCV
    # PyBullet returns images in BGRA format, so convert to RGB
    image_rgb = cv2.cvtColor(image_rgb, cv2.COLOR_RGBA2RGB)

    # Now convert the RGB image to Grayscale for processing
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)

    if i == 0:
        grid_points = find_grid(gray)
        init_satPos, init_satOrn = p.getBasePositionAndOrientation(cubeSatId)
        orn_thresh_min = init_satOrn[2] - 0.01
        orn_thresh_max = init_satOrn[2] + 0.01
        print(f"Initial Sat:\n Position: {init_satPos}\nOrientation: {init_satOrn}")

        # Perform Orientation manipulation
        torque = [0, 0, 120]  # Apply torque around Z-axis
        p.applyExternalTorque(cubeSatId, -1, torque, p.WORLD_FRAME)
    if i == 100:
        # Perform Orientation manipulation
        torque = [0, 0, -30]  # Apply torque around Z-axis
        p.applyExternalTorque(cubeSatId, -1, torque, p.WORLD_FRAME)
    if i == 1:
        for _ in range(3):
            x, y = random.randint(0, 4), random.randint(0, 4)
            temp_grid[x][y] = random.randint(25, 100)

    if i > 1:
        satPos, satOrn = p.getBasePositionAndOrientation(cubeSatId)
        if satOrn[2] > orn_thresh_min and satOrn[2] < orn_thresh_max:
            # Update the temperature grid
            temp_grid = update_fire(classifications,temp_grid)

    if i <= 1 or (satOrn[2] > orn_thresh_min and satOrn[2] < orn_thresh_max):
        # Update colors of the grid objects based on temperature
        update_colors_based_on_temp(objects, temp_grid)

        #classify_cells(gray,grid_corners)
        centroid_intensities = read_centroid_intensity(gray, grid_points, area_mode=True)
        #print(centroid_intensities)
        grid_intensities = [centroid_intensities[i:i + grid_size] for i in range(0, len(centroid_intensities), grid_size)]
        #print(grid_intensities)
        # Use the function to classify the centroid intensities

        classifications = classify_grid(grid_intensities)
        #print(classifications)
        # classification_array = [classifications[i:i + grid_size] for i in range(0, len(classifications), grid_size)]

        # Print the array with colored elements
        for row in classifications:
            for elem in row:
                print(f"{get_color(elem)}{elem}{ENDC}", end=' ')
            print()  # Newline after each row
        print()


    # Apply orientation correction
    apply_orientation_correction(cubeSatId, init_satOrn)
    time.sleep(1. / 240.)
    #time.sleep(2)

# Disconnect PyBullet
p.disconnect()
