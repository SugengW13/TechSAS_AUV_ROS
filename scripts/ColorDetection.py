#!/usr/bin/env python

import cv2
import numpy as np
import rospy
from std_msgs.msg import String

def setContour(image):  
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    
    return contours

def setBoundingBox(cnts, image):
    if len(cnts) > 0:
        centroid = max(cnts, key=cv2.contourArea)
        ((x, y), radius) = cv2.minEnclosingCircle(centroid)

        if radius > 10:
            cv2.circle(image, (int(x), int(y)), 2, (0, 255, 0), 2)
            cv2.circle(image, (int(x), int(y)), int(radius), (0, 255, 0), 2)
            cv2.line(image, (int(x), int(y)), (320, 240), (255, 0, 0), 2)
            return [x, y]
        else:
            return 'None'
        
    return 'None'

def getObjectPosition(image):
    arr = []
    dst = cv2.Canny(image, 50, 200, None, 3)

    linesP = cv2.HoughLinesP(dst, 1, np.pi / 180, 50, None, 50, 10)

    if linesP is not None:
        for i in range(0, len(linesP)):
            l = linesP[i][0]
            arr.append(l[1])
            arr.append(l[3])

    return np.min(arr)

def colorDetection(capture):
    pub = rospy.Publisher('coordinate', String, queue_size=10)
    rospy.init_node('publisher_coordinate', anonymous=True)
    rate = rospy.Rate(10)

    while not rospy.is_shutdown():
        _, frame = capture.read()

        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            lowerHsv = (20, 130, 80)
            upperHsv = (25, 255, 255)

            thresh = cv2.inRange(hsv, lowerHsv, upperHsv)
            
            contours = setContour(thresh)

            coordinate = setBoundingBox(contours, frame)

            yUpperCoordinate = getObjectPosition(thresh)

            if coordinate != 'None':
                str_coordinate = ' '.join(map(str, coordinate))
            else:
                str_coordinate = coordinate

            cv2.line(frame, (0, yUpperCoordinate), (640, yUpperCoordinate), (0, 0, 255), 1)
            
            cv2.circle(frame, (320, 240), 2, (255, 0, 0), 1)
            cv2.circle(frame, (320, 240), 25, (0, 0, 255), 1)
            cv2.circle(frame, (320, 240), 200, (0, 255, 0), 1)
            
            cv2.imshow('Frame', frame)
            cv2.imshow('Threshold', thresh)

            rospy.loginfo(str_coordinate + ' ' + str(yUpperCoordinate))
            pub.publish(str_coordinate + ' ' + str(yUpperCoordinate))

            rate.sleep()

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except:
            continue

    frame.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    try:
        colorDetection(camera)
    except rospy.ROSInterruptException:
        pass