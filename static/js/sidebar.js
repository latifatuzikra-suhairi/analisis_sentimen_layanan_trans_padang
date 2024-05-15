$(document).ready(function() {
    const sidebar = $(".sidebar");
    const closeBtn = $("#btn-toggle");
    const addBtn = $("#btnAddData");

    const closeAddBtn = $("#btnCloseAddData");
    const divAddData = $("#divAddData");
    const komentarTbl = $("#tabelKomentar");
    const fileInput = $("#fileInput");

    // inisiate div untuk menambah data komentar
    divAddData.hide();
    $('#btnSubmitFile').hide();
    $('#btnCancelSubmitFile').hide();

    // membuka div DataKomentar
    addBtn.click(function() {
        if (divAddData.is(":hidden")) {
            divAddData.slideDown();
        } else {
            divAddData.slideUp();
        }
    });

    // menutup div DataKomentar
    closeAddBtn.click(function() {
        fileInput.wrap('<form>').closest('form').get(0).reset();
        fileInput.unwrap();
        divAddData.slideUp();
        $('#fileName').text('pilih file .csv yang akan diunggah!');
        $('#btnPilihFile').show(); 
        $('#btnSubmitFile').hide(); $('#btnCancelSubmitFile').hide();
        $('#logo-upload-file').removeClass("bx-file-blank").addClass("bx-upload");
    });

    // fungsi untuk membuka laman upload file
    $("#btnPilihFile").click(function() {
        $("#fileInput").click();
    });

    // fungsi untuk cancel upload file
    $("#btnCancelSubmitFile").click(function() {
        fileInput.wrap('<form>').closest('form').get(0).reset();
        fileInput.unwrap();
        $('#fileName').text('pilih file .csv yang akan diunggah!');
        $('#btnPilihFile').show(); 
        $('#btnSubmitFile').hide(); $('#btnCancelSubmitFile').hide();
        $('#logo-upload-file').removeClass("bx-file-blank").addClass("bx-upload");
    })

    // upload file
    fileInput.on("change",  function() {
        console.log('changes')
        if (fileInput.prop('files').length > 0) {
            var fileName = fileInput.prop('files')[0].name;
            $('#fileName').text(fileName);
            $('#btnPilihFile').hide(); 
            $('#btnSubmitFile').show(); $('#btnCancelSubmitFile').show();
            $('#logo-upload-file').removeClass("bx-upload").addClass("bx-file-blank")
            console.log('File Terupload')
        } else {
            console.log('Tidak ada file yang diunggah.');
        }
    }); 

    // delete data
    $('#delete-button').click(function(e) {
        e.preventDefault();
        Swal.fire({
            title: "Anda yakin ingin menghapus data yang dipilih?",
            text: "Data yang telah dihapus tidak dapat dikembalikan",
            showDenyButton: true,
            confirmButtonText: "Ya",
            denyButtonText: "Tidak",
            icon: "warning"
        })
        .then((result) => {
            if (result.isConfirmed) {
                // Create an empty array to store the values
                var id_komentar = [];
                // Get checked checkboxes
                var checkedBoxes = $('input[type="checkbox"]:checked', komentarTbl.DataTable().rows().nodes());
                // Loop through each checkbox
                checkedBoxes.each(function() {
                    // Get the value
                    var value = $(this).val();
                    // Store the value in the array
                    id_komentar.push(value);
                });

                if(id_komentar.length === 0){
                    Swal.fire({
                        icon: "error",
                        title: "Hapus Data Komentar Gagal!",
                        text: "Anda belum memilih baris data yang ingin dihapus"
                    });
                }
                else{
                    // post data id_komentar ke python
                    $.ajax({
                        url: '/beranda/del_komentar', // route delete komentar
                        type: 'POST',
                        data: JSON.stringify(id_komentar), // mengirimkan array id_komentar dalam bentuk JSON
                        contentType: 'application/json',
        
                        success: function(response) {
                            if (response.redirect) {
                                Swal.fire({
                                    title: 'Hapus Data',
                                    text: response.msg,
                                    icon: response.action,
                                    showConfirmButton: false,
                                    timer: 1500  // tampilkan swal fire selama 1 detik
                                }).then(() => {
                                    // setelah swal fire ditutup, pindah ke URL baru
                                    window.location.href = response.redirectURL;
                                });
                    
                                // jika swal fire ditutup sebelum 1 detik, pindah ke URL baru setelah 1 detik
                                setTimeout(function() {
                                    window.location.href = response.redirectURL;
                                }, 1500);
                            }
                        }
                    });
                }
                
            } else {
                Swal.fire({
                    icon: "warning",
                    title: "Hapus Data Komentar Dibatalkan!"
                });
            }
        });
    });

    // btn klasifikasi
    $('#btnKlasifikasi').click(function(e){
        e.preventDefault();
        $('#spinnerOverlay').show();
        $('#spinnerOverlay').css('display', 'flex');

        $.ajax({
            url: '/beranda/klasifikasi',
            type: 'POST',
            success: function(response){
                if (response.redirect) {
                    Swal.fire({
                        title: 'Klasifikasi Data',
                        text: response.msg,
                        icon: response.action,
                        showConfirmButton: false,
                        timer: 1000  // tampilkan swal fire selama 1 detik
                    }).then(() => {
                        // setelah swal fire ditutup, pindah ke URL baru
                        window.location.href = response.redirectURL;
                    });
        
                    // jika swal fire ditutup sebelum 1 detik, pindah ke URL baru setelah 1 detik
                    setTimeout(function() {
                        window.location.href = response.redirectURL;
                    }, 1000);
                    $('#spinnerOverlay').hide();
                }
            },
            error: function(error){
                console.log(error);
                $('#spinnerOverlay').hide();
            }
        });
    });

    // mengatur max tanggal input
    var today = new Date();
    var dd = String(today.getDate()).padStart(2, '0');
    var mm = String(today.getMonth() + 1).padStart(2, '0'); // Bulan Januari adalah 0!
    var yyyy = today.getFullYear();

    today = yyyy + '-' + mm + '-' + dd;
    $("#inputTanggal").attr("max", today);

    // sidebar
    closeBtn.click(function() {
        sidebar.toggleClass("open");
        menuBtnChange();
    });

    $('#log_out').click(function(e) {
        e.preventDefault();
        Swal.fire({
            title: "Anda yakin ingin logout?",
            showDenyButton: true,
            confirmButtonText: "Ya",
            denyButtonText: "Tidak",
            icon: "warning"
        })
        .then((result) => {
            if (result.isConfirmed) {
                $.ajax({
                    url: '/logout',  // replace with your logout route
                    type: 'POST',
                    success: function(success) {
                        Swal.fire({
                            title: "Logout!",
                            text: "Anda berhasil logout!",
                            icon: "success"
                          })
                        .then((value) => {
                            // Redirect to login page after logout
                            window.location.href = "/login";  
                        });
                    },
                    error: function(error) {
                        console.log(error);
                        Swal.fire({
                            icon: "error",
                            title: "Oops! Terjadi Kesalahan"
                        });
                    }
                });
            } else {
                Swal.fire({
                    title: "Logout Dibatalkan!",
                    imageUrl: '../static/img/logo.png',
                    imageWidth: 400,
                    imageHeight: 200,
                    imageAlt: "Custom image"
                });
            }
        });
    });

    function menuBtnChange() {
        if(sidebar.hasClass("open")) {
            closeBtn.removeClass("bx-menu").addClass("bx-menu-alt-right");
        } else {
            closeBtn.removeClass("bx-menu-alt-right").addClass("bx-menu");
        }
    }

    var loc = window.location.pathname;
    $('.nav-list .page').each(function() {
        if ($(this).attr('href') == loc){
            $(this).addClass('active-page')
        }
    });

    // tabel komentar 
    komentarTbl.DataTable({
        columnDefs: [
            { width: '11%', targets: 1 } // Set lebar kolom kedua menjadi 20%
          ]
    });

});

