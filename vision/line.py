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
        self.last_center = None
        self.missed_frames = 0



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
                "error":None,
                "heading":0,
                "curvature":0,
                "skeleton":[],
                "mask":mask,
                "confidence":0.0

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

            error = (near_x-cx) / max(w / 2.0, 1.0)

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

            "mask":mask,
            "confidence":self._confidence(contour, skeleton, mask.shape)

        }



    def get_contour(self,mask):

        contours,_ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )


        if not contours:
            self.missed_frames += 1
            return None
        h, w = mask.shape
        candidatos = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < max(80, w * h * 0.001):
                continue
            x, y, cw, ch = cv2.boundingRect(contour)
            toca_base = y + ch >= int(h * 0.65) # era 0.78: na curva fechada a linha
            M = cv2.moments(contour)
            centro = M["m10"] / M["m00"] if M["m00"] else x + cw / 2
            continuidade = 1.0 if self.last_center is None else max(0.0, 1 - abs(centro - self.last_center) / (w * 0.5))
            orientacao = min(ch / max(cw, 1), 2.0) / 2.0
            score = area / (w * h) * 2 + continuidade + orientacao + (0.8 if toca_base else 0)
            if toca_base or continuidade > 0.55:     # era 0.75
                candidatos.append((score, contour, centro))
        if not candidatos:
            self.missed_frames += 1
            return None
        _, contour, self.last_center = max(candidatos, key=lambda item: item[0])
        self.missed_frames = 0
        return contour

    @staticmethod
    def _confidence(contour, skeleton, shape):
        h, w = shape
        area = cv2.contourArea(contour) / (h * w)
        return float(min(1.0, 0.35 + min(area * 8, 0.35) + 0.1 * len(skeleton)))




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
