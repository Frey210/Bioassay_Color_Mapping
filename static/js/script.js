// Fungsi untuk menampilkan bagian tertentu berdasarkan ID
function showSection(sectionId) {
    const sections = document.querySelectorAll('.content-section');
    sections.forEach(section => section.style.display = 'none'); // Sembunyikan semua bagian
    document.getElementById(sectionId).style.display = 'block'; // Tampilkan bagian yang dipilih

    const deteksiBtn = document.getElementById('deteksiBtn');
    const riwayatBtn = document.getElementById('riwayatBtn');

    // Tambah atau hapus kelas 'active' sesuai tombol yang dipilih
    if (sectionId === 'deteksi') {
        deteksiBtn.classList.add('active');
        riwayatBtn.classList.remove('active');
    } else {
        riwayatBtn.classList.add('active');
        deteksiBtn.classList.remove('active');
    }
}

// Variabel untuk menyimpan data sementara
let capturedImagePath = null;
let cameraRgb = [0, 0, 0];
let sensorRgb = [0, 0, 0];
let chart = null;

// Fungsi untuk menangkap data
function captureData() {
    fetch('/capture', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(`Error: ${data.error}`);
                return;
            }

            console.log('Image Path:', data.image_path); // Debugging path gambar

            // Perbarui variabel global dengan data yang diterima
            capturedImagePath = data.image_path;
            cameraRgb = data.camera_rgb; // Update nilai kamera RGB
            sensorRgb = data.sensor_rgb; // Update nilai sensor RGB

            // Tampilkan gambar dan nilai RGB
            document.getElementById('captured-image').src = capturedImagePath;
            document.getElementById('sensor-rgb').textContent = `Sensor RGB: R=${sensorRgb[0]} G=${sensorRgb[1]} B=${sensorRgb[2]}`;
            document.getElementById('camera-rgb').textContent = `Kamera RGB: R=${cameraRgb[0]} G=${cameraRgb[1]} B=${cameraRgb[2]}`;
        })
        .catch(err => {
            console.error('Error capturing data:', err);
        });
}

// Fungsi untuk menampilkan hasil prediksi
function showPredictionResult(prediction) {
    // Sembunyikan spinner setelah hasil prediksi muncul
    document.getElementById('loading').style.display = 'none';
    
    // Tampilkan hasil prediksi
    document.getElementById('density-result').textContent = prediction;
}

// Fungsi untuk mengirim data RGB dan nilai BC ke backend
function generateDensity() {
    // Tampilkan spinner loading saat proses dimulai
    document.getElementById('loading').style.display = 'block';

    // Ambil nilai dari radio button
    const bcElement = document.querySelector('input[name="bc"]:checked');
    if (!bcElement) {
        alert("Silakan pilih nilai BC terlebih dahulu!");
        return;
    }
    const bc = bcElement.value;

    // Validasi data sebelum dikirim
    if (!capturedImagePath || cameraRgb.every(val => val === 0) || sensorRgb.every(val => val === 0)) {
        alert("Pastikan Anda sudah menekan tombol 'Capture Data' terlebih dahulu.");
        return;
    }

    // Kirim data ke backend
    fetch('/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            camera_rgb: cameraRgb,
            sensor_rgb: sensorRgb,
            bc: bc,
            image_path: capturedImagePath
        })
    })
        .then(response => response.json())
        .then(data => {
            // Sembunyikan spinner loading setelah data diterima
            document.getElementById('loading').style.display = 'none';

            if (data.error) {
                alert(`Error: ${data.error}`);
            } else {
                // Mendapatkan kelas hasil prediksi dan menampilkan rentang
                const classLabel = data.density;  // Misalnya "S1", "S2", dll.
                
                // Mendefinisikan rentang nilai kelas
                const classRanges = {
                    S1: { min: 1.25, max: 9.5 },
                    S2: { min: 9.51, max: 15.75 },
                    S3: { min: 15.76, max: 21.5 },
                    S4: { min: 21.51, max: 33.75 },
                    S5: { min: 33.76, max: 58.5 }
                };

                // Menampilkan hasil prediksi dengan rentang nilai
                const range = classRanges[classLabel];
                const rangeText = `(${range.min} - ${range.max}) * 10^4 cell/ml`;
                
                // Menampilkan hasil prediksi di elemen 'density-result'
                document.getElementById('density-result').textContent = 
                    `Predicted Density: ${classLabel} ${rangeText}`;
            }
        })
        .catch(error => {
            // Sembunyikan spinner loading jika terjadi error
            document.getElementById('loading').style.display = 'none';
            console.error('Error:', error);
            alert('Terjadi kesalahan saat memproses data.');
        });
}


// Fungsi untuk mengonversi densitas ke nilai numerik
function convertDensityToValue(density) {
    const densityMap = {
        'S1': 1,
        'S2': 2,
        'S3': 3,
        'S4': 4,
        'S5': 5
    };
    return densityMap[density] || 0; // Default ke 0 jika tidak ada
}

// Fungsi untuk memperbarui grafik riwayat
function updateChart() {
    fetch('/history', { method: 'GET' })
        .then(response => response.json())
        .then(data => {
            const timestamps = data.map(item => item.timestamp);
            const densities = data.map(item => convertDensityToValue(item.density)); // Mengonversi densitas ke nilai numerik

            // Perbarui tabel riwayat
            updateTable(data);

            // Perbarui grafik
            if (chart) {
                chart.data.labels = timestamps;
                chart.data.datasets[0].data = densities;
                chart.update();
            } else {
                const ctx = document.getElementById('historyChart').getContext('2d');
                chart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: timestamps,
                        datasets: [{
                            label: 'Kepadatan Pakan (S1-S5)',
                            data: densities,
                            borderColor: 'rgba(75, 192, 192, 1)',
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            borderWidth: 1,
                            tension: 0.1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            x: {
                                title: {
                                    display: true,
                                    text: 'Waktu'
                                }
                            },
                            y: {
                                title: {
                                    display: true,
                                    text: 'Kepadatan Pakan (S1-S5)'
                                },
                                ticks: {
                                    beginAtZero: true,
                                    stepSize: 1,
                                    max: 5
                                },
                                scaleLabel: {
                                    display: true,
                                    labelString: 'Kepadatan (S1-S5)'
                                }
                            }
                        }
                    }
                });
            }
        })
        .catch(err => console.error('Error updating chart:', err));
}

// Fungsi untuk mengonversi densitas ke nilai numerik
function convertDensityToValue(density) {
    const densityMap = {
        'S1': 1,
        'S2': 2,
        'S3': 3,
        'S4': 4,
        'S5': 5
    };
    return densityMap[density] || 0; // Default ke 0 jika tidak ada
}

// Fungsi untuk memperbarui grafik riwayat
function updateChart() {
    fetch('/history', { method: 'GET' })
        .then(response => response.json())
        .then(data => {
            const timestamps = data.map(item => item.timestamp);
            const densities = data.map(item => convertDensityToValue(item.density)); // Mengonversi densitas ke nilai numerik

            // Perbarui tabel riwayat
            updateTable(data);

            // Perbarui grafik
            if (chart) {
                chart.data.labels = timestamps;
                chart.data.datasets[0].data = densities;
                chart.update();
            } else {
                const ctx = document.getElementById('historyChart').getContext('2d');
                chart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: timestamps,
                        datasets: [{
                            label: 'Kepadatan Pakan (S1-S5)',
                            data: densities,
                            borderColor: 'rgba(75, 192, 192, 1)',
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            borderWidth: 1,
                            tension: 0.1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            x: {
                                title: {
                                    display: true,
                                    text: 'Waktu'
                                }
                            },
                            y: {
                                title: {
                                    display: true,
                                    text: 'Kepadatan Pakan (S1-S5)'
                                },
                                ticks: {
                                    beginAtZero: true,
                                    stepSize: 1,
                                    max: 5
                                },
                                scaleLabel: {
                                    display: true,
                                    labelString: 'Kepadatan (S1-S5)'
                                }
                            }
                        }
                    }
                });
            }
        })
        .catch(err => console.error('Error updating chart:', err));
}

fetch('/history')
    .then(response => response.json())
    .then(data => {
        updateTable(data);  // Panggil fungsi untuk memperbarui tabel dengan data
    });

    function updateTable(data) {
        const tableBody = document.getElementById('historyTable').querySelector('tbody');
        tableBody.innerHTML = ''; // Kosongkan isi tabel
    
        data.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.timestamp}</td>
                <td>R=${item.camera_rgb[0].toFixed(3)} G=${item.camera_rgb[1].toFixed(3)} B=${item.camera_rgb[2].toFixed(3)}</td>
                <td>R=${item.sensor_rgb[0].toFixed(3)} G=${item.sensor_rgb[1].toFixed(3)} B=${item.sensor_rgb[2].toFixed(3)}</td>
                <td>${item.bc_value}</td>
                <td>${item.density}</td>
                <td><a href="${item.image_path}" target="_blank">Lihat Gambar</a></td>
            `;
            tableBody.appendChild(row);
        });
    }



// Inisialisasi halaman
document.addEventListener("DOMContentLoaded", function () {
    showSection('deteksi'); // Default ke bagian deteksi
    updateChart(); // Perbarui grafik saat halaman dimuat
});

function toggleExplanation() {
    var explanation = document.getElementById("classExplanation");
    // Toggle visibility of explanation
    if (explanation.style.display === "none" || explanation.style.display === "") {
        explanation.style.display = "block";
    } else {
        explanation.style.display = "none";
    }
}
