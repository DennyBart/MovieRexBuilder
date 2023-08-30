(define (script-fu-splice-images img1-path img2-path img3-path)
  (let* (
         (image1 (car (gimp-file-load RUN-NONINTERACTIVE img1-path img1-path)))
         (image2 (car (gimp-file-load RUN-NONINTERACTIVE img2-path img2-path)))
         (image3 (car (gimp-file-load RUN-NONINTERACTIVE img3-path img3-path)))

         (width (car (gimp-image-width image1)))
         (height (car (gimp-image-height image1)))

         (third-width (/ width 3))
         (output-image (car (gimp-image-new width height RGB)))
         (output-drawable (car (gimp-layer-new output-image width height RGB-IMAGE "Spliced" 100 NORMAL-MODE)))
        )
        
    (gimp-image-insert-layer output-image output-drawable 0 -1)
    
    ; Crop and copy from image1
    (let* ((drawable (car (gimp-image-get-active-layer image1))))
      (gimp-rect-select image1 0 0 third-width height CHANNEL-OP-REPLACE FALSE 0)
      (gimp-edit-copy drawable)
      (let ((floating-sel (car (gimp-edit-paste output-drawable FALSE))))
        (gimp-floating-sel-anchor floating-sel)))

    ; Crop and copy from image2
    (let* ((drawable (car (gimp-image-get-active-layer image2))))
      (gimp-rect-select image2 third-width 0 third-width height CHANNEL-OP-REPLACE FALSE 0)
      (gimp-edit-copy drawable)
      (let ((floating-sel (car (gimp-edit-paste output-drawable FALSE))))
        (gimp-layer-translate floating-sel third-width 0)
        (gimp-floating-sel-anchor floating-sel)))

    ; Crop and copy from image3
    (let* ((drawable (car (gimp-image-get-active-layer image3))))
      (gimp-rect-select image3 (* 2 third-width) 0 third-width height CHANNEL-OP-REPLACE FALSE 0)
      (gimp-edit-copy drawable)
      (let ((floating-sel (car (gimp-edit-paste output-drawable FALSE))))
        (gimp-layer-translate floating-sel (* 2 third-width) 0)
        (gimp-floating-sel-anchor floating-sel)))

    ; Add lines
    (gimp-context-set-foreground '(255 255 255))  ; Set the line color to white
    (gimp-paintbrush-default output-drawable 4 (cons-array '(third-width 0 third-width height) 'double))
    (gimp-paintbrush-default output-drawable 4 (cons-array `(* 2 third-width 0) `(* 2 third-width ,height) 'double))

    (gimp-display-new output-image)
  )
)

(script-fu-register "script-fu-splice-images"
                    "Splice Images"
                    "Splice images together."
                    "Your Name"
                    "Your Name"
                    "2023"
                    "RGB* GRAY*"
                    SF-FILENAME "Image 1 Path" ""
                    SF-FILENAME "Image 2 Path" ""
                    SF-FILENAME "Image 3 Path" ""
)

(script-fu-menu-register "script-fu-splice-images"
                         "<Image>/Filters/Custom")
