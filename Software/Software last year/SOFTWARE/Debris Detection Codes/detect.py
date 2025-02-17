# Created by Cian McDonnell for Cranfield CONDOR Satellite team 2023
# Place in a folder with a subfolder called "images" containing "test_image_1.jpg" and "test_image_2.jpg"


import cv2
import numpy as np


def center_of_mass(image): # calculate center of mass (or center of intensity more accurately) in an image
    # Wikipedia gives a nice formula for the center of mass based on the "moments" of the image - implement this
    m_00 = np.sum(image)
    print(np.shape(image))
    y_summed_image = np.sum(image,axis=0)
    weighted_x_sum = 0
    print("Y Summed Image has length "+str(len(y_summed_image)))
    x_summed_image = np.sum(image, axis=1)
    weighted_y_sum = 0
    print("X Summed Image has length "+str(len(x_summed_image)))
    for i in range(0,len(y_summed_image)):
        weighted_x_sum += i*y_summed_image[i]
    for j in range(0,len(x_summed_image)):
        weighted_y_sum += j*x_summed_image[j]
    return np.asarray([weighted_x_sum/m_00,weighted_y_sum/m_00])

def edge_detect(image): # Returns a Canny edge-detected image
    image_grey = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    image_blur = cv2.GaussianBlur(image_grey,(3,3),0)
    image_edged = cv2.Canny(image=image_blur,threshold1=100,threshold2=200)
    return image_edged

def display_com(image): #displays the center of mass of an image (be sure the image is in grayscale format or it will crash)
    com = center_of_mass(image)
    img_shape = np.shape(image)
    img_area = img_shape[0]*img_shape[1]
    print("Center of Mass: "+str(com))
    keypoint = cv2.KeyPoint(com[0], com[1], size=20*img_area/(24e5))
    image_with_com = cv2.drawKeypoints(image, [keypoint], np.array([]), (0, 0, 255),
                                        cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
    return image_with_com

# Read the original image
img1 = cv2.imread('images/test_image_1.jpg')
img2 = cv2.imread('images/test_image_2.jpg')

edges1 = edge_detect(img1)
edges2 = edge_detect(img2)


edges1_with_com = display_com(edges1)
edges2_with_com = display_com(edges2)

#cv2.imshow('Edge Detection 1', edges1_with_com)
#cv2.imshow('Edge Detection 2', edges2_with_com)
cv2.imwrite("edge2.jpg",edges2_with_com)
cv2.imwrite("edge1.jpg",edges1_with_com)

cv2.waitKey(0)
cv2.destroyAllWindows()