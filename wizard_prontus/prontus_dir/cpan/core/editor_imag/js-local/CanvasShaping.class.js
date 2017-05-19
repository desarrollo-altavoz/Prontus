// Objeto.
var CanvasShaping = function (canvas_id, canvas_width, canvas_height, image_path, image_w, image_h) {
    this.canvas_id = canvas_id;
    this.canvas_width = canvas_width;
    this.canvas_height = canvas_height;
    this.lastX = null;
    this.lastY = null;
    this.image = {
        object: new Image,
        real_width: image_w,
        real_height: image_h,
        relative_path: image_path
    };
    this.context = null;
    this.editor = document.getElementById(canvas_id);

    if (this.editor) {
        this.context = this.editor.getContext("2d");
        this.createImageObject();
    } else {
        console.error("Canvas no existe.");
    }
};

CanvasShaping.prototype.createImageObject = function () {
    var self = this; // closure.

    this.image.object.onload = function () {
        self.handleZoom(0);
        self.handleEvents();
    };

    this.image.object.src = this.image.relative_path;
    this.handleTransforms();
};

CanvasShaping.prototype.handleEvents = function () {
    this.lastX = this.canvas_width / 2;
    this.lastY = this.canvas_height / 2;

    var dragStart;
    var dragged;
    var self = this;

    this.editor.addEventListener('mousedown', function(evt) {
        // document.body.style.mozUserSelect = document.body.style.webkitUserSelect = document.body.style.userSelect = 'none';
        self.lastX = evt.offsetX || (evt.pageX - self.editor.offsetLeft);
        self.lastY = evt.offsetY || (evt.pageY - self.editor.offsetTopd);

        dragStart = self.context.transformedPoint(self.lastX, self.lastY);
        dragged = false;
    }, false);

    this.editor.addEventListener('mousemove', function(evt) {
        self.lastX = evt.offsetX || (evt.pageX - self.editor.offsetLeft);
        self.lastY = evt.offsetY || (evt.pageY - self.editor.offsetTop);
        dragged = true;

        if (dragStart) {
            var pt = self.context.transformedPoint(self.lastX, self.lastY);
            self.context.translate(pt.x - dragStart.x, pt.y - dragStart.y);
            self.handleZoom(0);
        }
    }, false);

    this.editor.addEventListener('mouseup', function(evt) {
        dragStart = null;
        if (!dragged) self.handleZoom(evt.shiftKey ? -1 : 1);
    });

    this.editor.addEventListener('DOMMouseScroll', function(evt) {
        var delta = evt.wheelDelta ? evt.wheelDelta/40 : evt.detail ? -evt.detail : 0;
        if (delta) self.handleZoom(delta);

        return evt.preventDefault() && false;
    }, false);

    this.editor.addEventListener('mousewheel', function(evt) {
        var delta = evt.wheelDelta ? evt.wheelDelta/40 : evt.detail ? -evt.detail : 0;
        if (delta) self.handleZoom(delta);

        return evt.preventDefault() && false;
    }, false);
};

CanvasShaping.prototype.getRealMouse = function (e) {
    var rect = this.image.object.getBoundingClientRect();

    return {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
    };
};

CanvasShaping.prototype.handleZoom = function (clicks) {
    var scaleFactor = 1.1;
    var pt = this.context.transformedPoint(this.lastX, this.lastY);
    var factor = Math.pow(scaleFactor, clicks);

    this.context.translate(pt.x, pt.y);
    this.context.scale(factor, factor);
    this.context.translate(-pt.x, -pt.y);

    this.drawImage(false);
};

CanvasShaping.prototype.drawImage = function (centrar) {
    var p1 = this.context.transformedPoint(0, 0);
    var p2 = this.context.transformedPoint(this.canvas_width, this.canvas_height);
    this.context.clearRect(p1.x, p1.y, (p2.x - p1.x), (p2.y - p1.y));

    this.context.save();
    this.context.setTransform(1, 0, 0, 1, 0, 0);
    this.context.clearRect(0, 0, this.canvas_width, this.canvas_height);
    this.context.restore();
    // this.context.resetTransform();

    if (typeof centrar !== 'undefined' && centrar) {
        var hRatio = this.canvas_width / this.image.real_width;
        var vRatio = this.canvas_height / this.image.real_height;
        var ratio = Math.min(hRatio, vRatio);
        var newW = (this.image.real_width * ratio);
        var newH = (this.image.real_height * ratio);

        // Si queda mas grande, no utilizar esos valores.
        if (newW > this.image.real_width || newH > this.image.real_height) {
            newW = this.image.real_width;
            newH = this.image.real_height;
        }

        // Valores para centrar la imagen en el canvas.
        var centerShift_x = (this.canvas_width - newW) / 2;
        var centerShift_y = (this.canvas_height - newH) / 2;

        this.lastX = centerShift_x;
        this.lastY = centerShift_y;

        this.context.drawImage(this.image.object, 0, 0, this.image.real_width, this.image.real_height,
            centerShift_x, centerShift_y, newW, newH);
    } else {
        this.context.drawImage(this.image.object, 0, 0);
    }
};

CanvasShaping.prototype.handleTransforms = function () {
    var svg = document.createElementNS("http://www.w3.org/2000/svg",'svg');
    var xform = svg.createSVGMatrix();
    var savedTransforms = [];
    var save = this.context.save;
    var restore = this.context.restore;
    var scale = this.context.scale;
    var rotate = this.context.rotate;
    var translate = this.context.translate;
    var transform = this.context.transform;
    var setTransform = this.context.setTransform;
    var pt  = svg.createSVGPoint();
    var self = this; // closure.

    this.context.getTransform = function() {
        return xform;
    };

    this.context.save = function() {
        savedTransforms.push(xform.translate(0, 0));

        return save.call(self.context);
    };

    this.context.restore = function() {
        xform = savedTransforms.pop();

        return restore.call(self.context);
    };

    this.context.scale = function(sx, sy){
        xform = xform.scaleNonUniform(sx, sy);

        return scale.call(self.context, sx, sy);
    };

    this.context.rotate = function(radians) {
        xform = xform.rotate(radians * 180 / Math.PI);

        return rotate.call(self.context, radians);
    };

    this.context.translate = function(dx, dy) {
        xform = xform.translate(dx, dy);

        return translate.call(self.context, dx, dy);
    };

    this.context.transform = function(a, b, c, d, e, f) {
        var m2 = svg.createSVGMatrix();
        m2.a = a;
        m2.b = b;
        m2.c = c;
        m2.d = d;
        m2.e = e;
        m2.f = f;
        xform = xform.multiply(m2);

        return transform.call(self.context, a, b, c, d, e, f);
    };

    this.context.setTransform = function(a, b, c, d, e, f) {
        xform.a = a;
        xform.b = b;
        xform.c = c;
        xform.d = d;
        xform.e = e;
        xform.f = f;

        return setTransform.call(self.context, a, b, c, d, e, f);
    };

    this.context.transformedPoint = function(x,y) {
        pt.x = x;
        pt.y = y;

        return pt.matrixTransform(xform.inverse());
    };
};
