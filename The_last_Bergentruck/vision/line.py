#line

import cv2
import numpy as np


class LineDetector:


    def __init__(self):

        # ajustar depois

        self.low = np.array(
            [0,0,0]
        )

        self.high = np.array(
            [180,255,80]
        )



    def detect(self,hsv):


        mask = cv2.inRange(
            hsv,
            self.low,
            self.high
        )


        mask = cv2.morphologyEx(
            mask,
            cv2.MORPH_OPEN,
            np.ones((5,5),np.uint8)
        )


        contour = self.get_contour(mask)



        if contour is None:

            return {

                "found":False,
                "error":0,
                "heading":0,
                "curvature":0,
                "skeleton":[],
                "mask":mask

            }



        h,w = mask.shape


        cx = w//2



        skeleton = self.get_skeleton(
            contour,
            h
        )


        # erro perto do robô

        if skeleton:

            near_x,near_y = skeleton[0]

            error = near_x-cx

        else:

            error = 0



        # ponto de previsão

        look = self.look_ahead(
            skeleton
        )



        heading = 0


        if look:

            lx,ly = look


            dx = lx-cx

            dy = h-ly


            heading=np.arctan2(
                dx,
                dy
            )



        curvature = self.curvature(
            skeleton
        )


        return {

            "found":True,

            "error":error,

            "heading":heading,

            "curvature":curvature,

            "skeleton":skeleton,

            "mask":mask

        }



    def get_contour(self,mask):

        contours,_ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )


        if not contours:
            return None


        return max(
            contours,
            key=cv2.contourArea
        )




    def get_skeleton(self,contour,h):


        pts=[]


        rows=[0.85,0.70,0.55,0.40]


        data=contour[:,0,:]


        for r in rows:

            y=int(h*r)


            near=data[
                abs(data[:,1]-y)<10
            ]


            if len(near)>0:

                x=int(
                    np.mean(
                        near[:,0]
                    )
                )

                pts.append(
                    (x,y)
                )


        return pts




    def look_ahead(self,skeleton):


        if len(skeleton)<2:

            return None


        # ponto mais distante

        return skeleton[-1]




    def curvature(self,pts):


        if len(pts)<3:

            return 0


        x=[
            p[0]
            for p in pts
        ]

        y=[
            p[1]
            for p in pts
        ]


        try:

            coef=np.polyfit(
                y,
                x,
                2
            )


            return coef[0]


        except:

            return 0
