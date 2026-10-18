import Foundation
import Vision
import AppKit

// Struttura dati per singolo blocco di testo riconosciuto
struct TextBlock: Codable {
    let text: String
    let y: Double       // 0.0 (alto) -> 1.0 (basso)
    let x: Double       // 0.0 (sinistra) -> 1.0 (destra)
    let w: Double
    let h: Double
    let confidence: Float
}

guard CommandLine.arguments.count > 2 else {
    print("Uso: ocr_batch_engine <cartella_foto> <file_output_json> [max_count]")
    exit(1)
}

let inputDir = CommandLine.arguments[1]
let outputFile = CommandLine.arguments[2]
let maxLimit = CommandLine.arguments.count > 3 ? Int(CommandLine.arguments[3]) : nil

let fileManager = FileManager.default
guard let enumerator = fileManager.enumerator(atPath: inputDir) else {
    print("Errore: impossibile aprire la cartella \(inputDir)")
    exit(1)
}

var allFiles: [String] = []
while let element = enumerator.nextObject() as? String {
    let lower = element.lowercased()
    if (lower.hasSuffix(".jpg") || lower.hasSuffix(".jpeg") || lower.hasSuffix(".png")) && !lower.contains("_thumb") {
        allFiles.append((inputDir as NSString).appendingPathComponent(element))
    }
}

allFiles.sort()
if let limit = maxLimit, limit < allFiles.count {
    allFiles = Array(allFiles.prefix(limit))
}

let total = allFiles.count
print("📸 Trovate \(total) immagini full-size da elaborare...")

let lock = NSLock()
var results: [String: [TextBlock]] = [:]

// Carica risultati precedenti se esistono già (modalità resume continua)
if fileManager.fileExists(atPath: outputFile),
   let existingData = try? Data(contentsOf: URL(fileURLWithPath: outputFile)),
   let existing = try? JSONDecoder().decode([String: [TextBlock]].self, from: existingData) {
    results = existing
    print("🔄 Ripresa da cache: già elaborate \(results.count)/\(total) immagini.")
}

let remainingFiles = allFiles.filter { results[$0] == nil }
print("⚡ Da processare in questo batch: \(remainingFiles.count) immagini...")

if remainingFiles.isEmpty {
    print("✅ Tutte le immagini sono già state elaborate!")
    exit(0)
}

// Coda con concorrenza controllata a 8 thread per non saturare i file descriptors del SO
let queue = OperationQueue()
queue.maxConcurrentOperationCount = 8

var processed = 0
let progressStep = 50

for path in remainingFiles {
    queue.addOperation {
        autoreleasepool {
            guard let image = NSImage(contentsOfFile: path),
                  let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
                return
            }
            
            var blocks: [TextBlock] = []
            let request = VNRecognizeTextRequest { req, error in
                guard let observations = req.results as? [VNRecognizedTextObservation] else { return }
                for obs in observations {
                    if let candidate = obs.topCandidates(1).first {
                        let topY = 1.0 - Double(obs.boundingBox.origin.y + obs.boundingBox.size.height)
                        let leftX = Double(obs.boundingBox.origin.x)
                        let block = TextBlock(
                            text: candidate.string,
                            y: topY,
                            x: leftX,
                            w: Double(obs.boundingBox.size.width),
                            h: Double(obs.boundingBox.size.height),
                            confidence: candidate.confidence
                        )
                        blocks.append(block)
                    }
                }
            }
            request.recognitionLanguages = ["it-IT", "en-US"]
            request.recognitionLevel = .accurate
            request.usesLanguageCorrection = true
            
            let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
            try? handler.perform([request])
            
            blocks.sort { $0.y < $1.y }
            
            lock.lock()
            results[path] = blocks
            processed += 1
            let currentProcessed = processed
            let shouldSave = (currentProcessed % progressStep == 0) || (currentProcessed == remainingFiles.count)
            lock.unlock()
            
            if shouldSave {
                lock.lock()
                if let data = try? JSONEncoder().encode(results) {
                    try? data.write(to: URL(fileURLWithPath: outputFile))
                }
                let pct = Double(results.count) / Double(total) * 100.0
                print(String(format: "🚀 Progresso: %d/%d (%.1f%%) completate.", results.count, total, pct))
                lock.unlock()
            }
        }
    }
}

queue.waitUntilAllOperationsAreFinished()

// Salvataggio finale
if let data = try? JSONEncoder().encode(results) {
    try? data.write(to: URL(fileURLWithPath: outputFile))
}
print("✅ OCR completato con successo su \(results.count) immagini! Salvato in: \(outputFile)")
