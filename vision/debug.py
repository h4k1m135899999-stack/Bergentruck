# debug

import cv2


class Debug:


    def __init__(self):
        pass



    def draw(
        self,
        frame,
        vision
    ):

        img = frame.copy()


        h,w = img.shape[:2]


        centro = w//2



        # ==================================================
        # LINHA CENTRAL DA CÂMERA
        # ==================================================

        cv2.line(
            img,
            (centro,0),
            (centro,h),
            (0,255,255),
            2
        )



        # ==================================================
        # LOOK AHEAD / ESQUELETO DA LINHA
        # ==================================================

        if vision.skeleton:


            for i,p in enumerate(vision.skeleton):

                x,y = p


                # ponto mais distante fica vermelho

                if i == len(vision.skeleton)-1:

                    color=(0,0,255)

                else:

                    color=(0,255,0)



                cv2.circle(
                    img,
                    (x,y),
                    6,
                    color,
                    -1
                )



            # linha ligando pontos

            for i in range(len(vision.skeleton)-1):

                cv2.line(
                    img,
                    vision.skeleton[i],
                    vision.skeleton[i+1],
                    (255,0,0),
                    2
                )




        # ==================================================
        # ERRO DA LINHA
        # ==================================================

        if vision.line_found:


            erro_x = int(centro + vision.center_error * (w / 2))


            cv2.line(
                img,
                (centro,h-30),
                (erro_x,h-30),
                (0,0,255),
                3
            )


            cv2.putText(
                img,
                f"erro: {vision.center_error:.1f}",
                (10,h-50),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255,255,255),
                2
            )



        # ==================================================
        # HEADING LOOK AHEAD
        # ==================================================

        cv2.putText(
            img,
            f"heading: {vision.heading:.3f}",
            (10,30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255,255,255),
            2
        )


        cv2.putText(
            img,
            f"curvature: {vision.curvature:.4f}",
            (10,55),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255,255,255),
            2
        )




        # ==================================================
        # VERDES
        # ==================================================

        if vision.green_left:

            cv2.putText(
                img,
                "VERDE ESQ",
                (10,90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0,255,0),
                2
            )


        if vision.green_right:

            cv2.putText(
                img,
                "VERDE DIR",
                (10,120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0,255,0),
                2
            )




        # ==================================================
        # FITAS
        # ==================================================

        y=150


        if vision.red:

            cv2.putText(
                img,
                "CHEGADA VERMELHA",
                (10,y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0,0,255),
                2
            )

            y+=30



        if vision.silver:

            cv2.putText(
                img,
                "ENTRADA PRATA",
                (10,y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (200,200,200),
                2
            )

            y+=30



        if vision.black_exit:

            cv2.putText(
                img,
                "SAIDA PRETA",
                (10,y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (100,100,100),
                2
            )




        # ==================================================
        # OBSTÁCULO
        # ==================================================

        if vision.obstacle:

            if vision.obstacle_bbox:
                x, y_box, bw, bh = vision.obstacle_bbox
                cv2.rectangle(img, (x, y_box), (x + bw, y_box + bh), (0, 140, 255), 2)
            info = vision.obstacle_info or {}
            confidence = info.get("confidence", 0.0)

            cv2.putText(
                img,
                "OBSTACULO",
                (10,h-90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0,140,255),
                3
            )
            cv2.putText(img, f"score: {confidence:.2f} {info.get('evidence', {})}",
                        (10, h - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 140, 255), 1)




        # ==================================================
        # VÍTIMA
        # ==================================================

        if vision.victim_position:


            x,y = vision.victim_position


            cv2.circle(
                img,
                (x,y),
                15,
                (255,0,255),
                3
            )


            cv2.putText(
                img,
                f"{vision.victim_type} - {vision.victim_distance_mm:.0f} mm"
                if vision.victim_distance_mm is not None
                else str(vision.victim_type),
                (x+20,y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255,0,255),
                2
            )




        return img
