import Foundation
import Vision
import AppKit

let args = CommandLine.arguments
guard args.count > 1 else {
    print("Usage: ocr_runner <image_path>")
    exit(1)
}

let imagePath = args[1]
guard let image = NSImage(contentsOfFile: imagePath),
      let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    print("Error: cannot load image \(imagePath)")
    exit(1)
}

let semaphore = DispatchSemaphore(value: 0)
let request = VNRecognizeTextRequest { request, error in
    defer { semaphore.signal() }
    if let err = error {
        print("Vision error: \(err)")
        return
    }
    guard let observations = request.results as? [VNRecognizedTextObservation] else { return }
    for obs in observations {
        if let top = obs.topCandidates(1).first {
            print(top.string)
        }
    }
}
request.recognitionLanguages = ["it-IT", "en-US"]
request.recognitionLevel = .accurate
request.usesLanguageCorrection = true

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
do {
    try handler.perform([request])
} catch {
    print("Handler error: \(error)")
    semaphore.signal()
}
_ = semaphore.wait(timeout: .distantFuture)
