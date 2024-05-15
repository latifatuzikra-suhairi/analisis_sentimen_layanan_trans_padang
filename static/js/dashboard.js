$(document).ready(function() {
    // inisialisasi awal
    var start_date; 
    var end_date;

    // nilai default wordcloud
    let topikWordcloudNeg = $('#selectWordcloudNeg').val();
    let topikWordcloudPos = $('#selectWordcloudPos').val();

    // dashboard
    $('#dateRangePicker').daterangepicker({
        "showDropdowns": true,
        "minYear": 2021,
        "maxDate": new Date(),
        "startDate": "01/01/2021",
        "endDate": moment(),
        "opens": "right",
        "locale": {
            "format": "DD/MM/YYYY",
            "separator": " - ",
            "daysOfWeek": [
                "Mg",
                "Sn",
                "Sl",
                "Rb",
                "Km",
                "Jm",
                "Sb"
            ],
            "monthNames": [
                "Januari",
                "Februari",
                "Maret",
                "April",
                "Mei",
                "Juni",
                "Juli",
                "Agustus",
                "September",
                "Oktober",
                "November",
                "Desember"
            ],
            "firstDay": 1
        }
    }, function(start, end) {
        start_date = start.format('YYYY/MM/DD');
        end_date = end.format('YYYY/MM/DD');
        fetchDataDashboard(start_date, end_date);
    });

    // fetch min max date based on db
    function fetchMinMaxDate(){
        $.ajax({
            url: '/get_min_max_dates',  // URL endpoint yang mengembalikan tanggal min dan max
            type: 'GET',
            success: function(data) {
                // format tanggal menjadi 'YYYY/MM/DD'
                start_date = moment(data.min_date).format('YYYY/MM/DD');
                end_date = moment(data.max_date).format('YYYY/MM/DD');

                // set tanggal pada saat start halaman awal beranda
                $('#dateRangePicker').data('daterangepicker').setStartDate(moment(data.min_date).format('DD/MM/YYYY'));
                $('#dateRangePicker').data('daterangepicker').setEndDate(moment(data.max_date).format('DD/MM/YYYY'));

                fetchDataDashboard(start_date, end_date);
            },
            error: function(XMLHttpRequest, errorThrown) { 
                alert("Error: " + errorThrown); 
            }
        });
    }
    fetchMinMaxDate()

    // fetch data dashboard
    function fetchDataDashboard(start, end){
        $.ajax({
            url: '/dashboard_data',
            type: 'POST',
            data: {
                start_date: start,
                end_date: end
            },
            success: function(data) {
                if(data.hasOwnProperty('action')) {
                    if(data.hasOwnProperty('user')){
                        if(data.user == "auth"){
                            console.log(data)
                            Swal.fire({
                                title: 'Dashboard',
                                text: data.msg,
                                icon: data.action,
                                showConfirmButton: true,
                                timer: 4000  // tampilkan swal fire selama 4 detik
                            }).then(() => {
                                // setelah swal fire ditutup, load
                                window.location.href = '/beranda';
                            });
                
                            // jika swal fire ditutup sebelum 4 detik, load
                            setTimeout(function() {
                                window.location.href = '/beranda';
                            }, 4000);
                        }
                        else if(data.user == "not_auth"){
                            Swal.fire({
                                title: 'Dashboard',
                                text: data.msg,
                                icon: data.action,
                                showConfirmButton: true,
                                timer: 4000  // tampilkan swal fire selama 4 detik
                            }).then(() => {
                                // setelah swal fire ditutup, load
                                window.location.href = '/login';
                            });
                
                            // jika swal fire ditutup sebelum 4 detik, load
                            setTimeout(function() {
                                window.location.href = '/login';
                            }, 4000);
                        }
                    } 
                    else{
                        Swal.fire({
                            title: 'Dashboard',
                            text: data.msg,
                            icon: data.action,
                            showConfirmButton: true,
                            timer: 4000  // tampilkan swal fire selama 4 detik
                        }).then(() => {
                            // setelah swal fire ditutup, load
                            location.reload();
                        });
            
                        // jika swal fire ditutup sebelum 3 detik, load
                        setTimeout(function() {
                            location.reload();
                        }, 4000);
                    }
                }
                else{
                    $("#c_kom").text(data.c_kom);
                    $("#c_op").text(data.c_op);
                    $("#c_nop").text(data.c_nop);
                    $("#c_pos").text(data.c_pos);
                    $("#c_neg").text(data.c_neg);
                    Plotly.newPlot('fig1', JSON.parse(data.fig1), {responsive: true});
                    Plotly.newPlot('fig2', JSON.parse(data.fig2), {responsive: true});
                    Plotly.newPlot('fig3', JSON.parse(data.fig3), {responsive: true});
                    Plotly.newPlot('fig4', JSON.parse(data.fig4), {responsive: true});

                    // datatable
                    var data_komentar = JSON.parse(data.data);
                    var table = $('#tabelCuplikanKomentar').DataTable({
                        "retrieve": true,
                        "lengthMenu": [[10, 25, -1], [10, 25, "All"]],
                        "scrollY": '490px',
                        "scrollCollapse": true,
                    });

                    $('#filter').on('change', function() {
                        // Filter tabel berdasarkan pilihan
                        var val = $.fn.dataTable.util.escapeRegex($(this).val());
                        table.column(2).search(val ? '^'+val+'$' : '', true, false).draw();
                    });

                    // Hapus data lama
                    table.clear().draw();

                    // Tambahkan data ke tabel
                    for(let i = 0; i < data_komentar.length; i++) {
                        let opini, topik, sentimen;
                        let css_opini, css_sentimen, css_aspek;

                        if (data_komentar[i]['opini'] == 1) {opini = "Opini"; css_opini = "badge-primary"; }
                        else if (data_komentar[i]['opini'] == 0) { opini = "Non Opini"; css_opini = "badge-danger"; }
                        else {opini = "--"; css_opini = "badge-missing";}

                        if (data_komentar[i]['topik'] == 1) {topik = "Isu Waktu Operasional"; css_aspek = "badge-primary";}
                        else if (data_komentar[i]['topik'] == 2) {topik = "Isu Halte"; css_aspek = "badge-primary";} 
                        else if (data_komentar[i]['topik'] == 3) {topik = "Isu Rute"; css_aspek = "badge-primary";}
                        else if (data_komentar[i]['topik'] == 4) {topik = "Isu Pembayaran"; css_aspek = "badge-primary";}
                        else if (data_komentar[i]['topik'] == 5) {topik = "Isu Perawatan Bus"; css_aspek = "badge-primary";}
                        else if (data_komentar[i]['topik'] == 6) {topik = "Isu Transit"; css_aspek = "badge-primary";}
                        else if (data_komentar[i]['topik'] == 7) {topik = "Isu Petugas"; css_aspek = "badge-primary";}
                        else if (data_komentar[i]['topik'] == 0) {topik = "Lainnya"; css_aspek = "badge-danger";}
                        else {topik = "--"; css_aspek = "badge-missing";}
                        
                        if (data_komentar[i]['sentimen'] == 1) {sentimen = "Positif"; css_sentimen = "badge-primary";}
                        else if (data_komentar[i]['sentimen'] == 0) {sentimen = "Negatif"; css_sentimen = "badge-danger";}
                        else {sentimen = "--"; css_sentimen = "badge-missing";}

                        table.row.add([
                            i+1,
                            data_komentar[i]['komentar'],
                            '<span class="badge ' + css_opini + ' text-wrap">' + opini + '</span>',
                            '<span class="badge ' + css_aspek + ' text-wrap">' + topik + '</span>',
                            '<span class="badge ' + css_sentimen + ' text-wrap">' + sentimen + '</span>',
                        ]).draw();
                    }
                    fetchWordCloud(start_date, end_date, topikWordcloudNeg);
                    
                    $('.skeleton').removeClass('skeleton');
                }
            },
            error: function(XMLHttpRequest, errorThrown) { 
                alert("Error: " + errorThrown); 
            }
        });
    }
    
    // nilai wordcloud ketika berubah
    $('#selectWordcloudNeg').change(function() {
        topikWordcloudNeg = $(this).val();
        fetchWordCloudNeg(start_date, end_date, topikWordcloudNeg);
      });

    $('#selectWordcloudPos').change(function() {
        topikWordcloudPos = $(this).val();
        fetchWordCloudPos(start_date, end_date, topikWordcloudPos);
    });

    function fetchWordCloudPos(start_date, end_date, topik){
        $("#wordcloud_pos_alert").addClass("d-none");
        $('#spinnerWordCloudPos').show();
        $('#spinnerWordCloudPos').css('display', 'flex');
        $("#wordcloud_pos").addClass("d-none");
        
        $.ajax({
            url: '/wordcloud_pos',
            type: 'POST',
            data: {
                start_date: start_date,
                end_date: end_date,
                topik: topik
            }, 
            success: function(response) {
                if(response.hasOwnProperty('msg')) { 
                    $('#wordcloud_pos_alert').text(response.msg);
                    $("#wordcloud_pos").addClass("d-none");
                    $("#wordcloud_pos_alert").removeClass("d-none");
                    $('#spinnerWordCloudPos').hide();
                }
                else{
                    $("#wordcloud_pos").removeClass("d-none");
                    $("#wordcloud_pos_alert").addClass("d-none");
                    $('#wordcloud_pos').attr('src', 'data:image/png;base64,' + response.wordcloud_pos);
                    $('#spinnerWordCloudPos').hide();
                }
            }
        })
    }

    function fetchWordCloudNeg(start_date, end_date, topik){
        $("#wordcloud_neg_alert").addClass("d-none");
        $('#spinnerWordCloudNeg').show();
        $('#spinnerWordCloudNeg').css('display', 'flex');
        $("#wordcloud_neg").addClass("d-none");

        $.ajax({
            url: '/wordcloud_neg',
            type: 'POST',
            data: {
                start_date: start_date,
                end_date: end_date,
                topik: topik
            }, 
            success: function(response) {
                if(response.hasOwnProperty('msg')) { 
                    $('#wordcloud_neg_alert').text(response.msg);
                    $("#wordcloud_neg").addClass("d-none");
                    $("#wordcloud_neg_alert").removeClass("d-none");
                    $('#spinnerWordCloudNeg').hide();
                }
                else{
                    $("#wordcloud_neg").removeClass("d-none");
                    $("#wordcloud_neg_alert").addClass("d-none");
                    $('#wordcloud_neg').attr('src', 'data:image/png;base64,' + response.wordcloud_neg);
                    $('#spinnerWordCloudNeg').hide();
                    
                }
            }
        })
    }

    function fetchWordCloud(start_date, end_date, topik){
        $("#wordcloud_neg_alert").addClass("d-none");
        $('#spinnerWordCloudNeg').show();
        $('#spinnerWordCloudNeg').css('display', 'flex');
        $("#wordcloud_neg").addClass("d-none");

        $("#wordcloud_pos_alert").addClass("d-none");
        $('#spinnerWordCloudPos').show();
        $('#spinnerWordCloudPos').css('display', 'flex');
        $("#wordcloud_pos").addClass("d-none");

        $.ajax({
            url: '/wordcloud',
            type: 'POST',
            data: {
                start_date: start_date,
                end_date: end_date,
                topik: topik
            }, 
            success: function(response) {
                if(response.hasOwnProperty('msg')) { 
                    $('#wordcloud_neg_alert').text(response.msg);
                    $("#wordcloud_neg").addClass("d-none");
                    $("#wordcloud_neg_alert").removeClass("d-none");
                    $('#spinnerWordCloudNeg').hide();

                    $('#wordcloud_pos_alert').text(response.msg);
                    $("#wordcloud_pos").addClass("d-none");
                    $("#wordcloud_pos_alert").removeClass("d-none");
                    $('#spinnerWordCloudPos').hide();
                }
                else{
                    $("#wordcloud_neg").removeClass("d-none");
                    $("#wordcloud_neg_alert").addClass("d-none");
                    $('#wordcloud_neg').attr('src', 'data:image/png;base64,' + response.wordcloud_pos);
                    $('#spinnerWordCloudNeg').hide();

                    $("#wordcloud_pos").removeClass("d-none");
                    $("#wordcloud_pos_alert").addClass("d-none");
                    $('#wordcloud_pos').attr('src', 'data:image/png;base64,' + response.wordcloud_neg);
                    $('#spinnerWordCloudPos').hide();
                    
                }
            }
        })
    }



});


