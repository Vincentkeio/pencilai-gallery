<?php
/**
 * Minimal, fixed header for the open-source export.
 * (The production header file in the uploaded archive contains pasted markdown and may break rendering.)
 */
?><!DOCTYPE html>
<html class="no-js" <?php language_attributes(); ?>>
<head>
	<meta charset="<?php bloginfo('charset'); ?>">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
	<main id="site-content" role="main">
