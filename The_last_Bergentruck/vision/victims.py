# victims

import cv2
import numpy as np


class VictimDetector:


    def __init__(self):

        # =====================================
        # VÍTIMA PRATA
        # =====================================
        #
        # Prata normalmente:
        # - pouco colorida
        # - brilho alto
        #

        self.silver_low = np.array(
            [0, 0, 130]
        )

        self.silver_high = np.array(
            [180, 70, 255]
        )



        # =====================================
        # VÍTIMA PRETA
        # =====================================

        self.dark_low = np.array(
            [0,0,0]
        )

        self.dark_high = np.array(
            [180,255,70]
        )



    def detect(self,hsv):


        silver = self.detect_color(
            hsv,
            self.silver_low,
            self.silver_high
        )


        dark = self.detect_color(
            hsv,
            self.dark_low,
            self.dark_high
        )



        # prioridade:
        #
        # prata = viva
        # preta = morta
        #

        if silver is not None:


            return {

                "found":True,

                "type":"silver",

                "position":silver["position"],

                "diameter_px":silver["diameter_px"]

            }



        if dark is not None:


            return {

                "found":True,

                "type":"dark",

                "position":dark["position"],

                "diameter_px":dark["diameter_px"]

            }



        return {

            "found":False,

            "type":None,

            "position":None,

            "diameter_px":None

        }





    def detect_color(
            self,
            hsv,
            low,
            high
    ):


        mask=cv2.inRange(
            hsv,
            low,
            high
        )


        mask=self.clean(mask)



        contours,_=cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )


        if not contours:

            return None



        # pega maior objeto

        contour=max(
            contours,
            key=cv2.contourArea
        )



        area=cv2.contourArea(
            contour
        )


        # elimina ruído

        if area < 80:

            return None



        x,y,w,h=cv2.boundingRect(
            contour
        )



        # evita pegar linha ou manchas grandes

        ratio=w/max(h,1)


        if ratio > 3:

            return None



        M=cv2.moments(
            contour
        )


        if M["m00"]==0:

            return None



        cx=int(
            M["m10"]/
            M["m00"]
        )


        cy=int(
            M["m01"]/
            M["m00"]
        )



        return {
            "position": (cx, cy),
            "diameter_px": max(w, h),
        }





    def clean(self,mask):


        kernel=np.ones(
            (3,3),
            np.uint8
        )


        return cv2.morphologyEx(
            mask,
            cv2.MORPH_OPEN,
            kernel
        )
