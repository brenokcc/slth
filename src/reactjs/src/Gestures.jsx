function detectSwipe(element, f) {
    var detect = {
        startX: 0,
        startY: 0,
        endX: 0,
        endY: 0,
        minX: 30,   // min X swipe for horizontal swipe
        maxX: 30,   // max X difference for vertical swipe
        minY: 50,   // min Y swipe for vertial swipe
        maxY: 60    // max Y difference for horizontal swipe
    },
        direction = null;

    element.addEventListener('touchstart', function (event) {
        var touch = event.touches[0];
        detect.startX = touch.screenX;
        detect.startY = touch.screenY;
    });

    element.addEventListener('touchmove', function (event) {
        //event.preventDefault();
        var touch = event.touches[0];
        detect.endX = touch.screenX;
        detect.endY = touch.screenY;
    });

    element.addEventListener('touchend', function (event) {
        if (
            // Horizontal move.
            (Math.abs(detect.endX - detect.startX) > detect.minX)
                && (Math.abs(detect.endY - detect.startY) < detect.maxY)
        ) {
            direction = (detect.endX > detect.startX) ? 'right' : 'left';
        } else if (
            // Vertical move.
            (Math.abs(detect.endY - detect.startY) > detect.minY)
                && (Math.abs(detect.endX - detect.startX) < detect.maxX)
        ) {
            direction = (detect.endY > detect.startY) ? 'down' : 'up';
        }

        if ((direction !== null) && (typeof f === 'function')) {
            f(element, direction);
        }
    });
}

export {detectSwipe};
export default detectSwipe;
